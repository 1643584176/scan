# 实验J88: 数据面 ACL 验证 — 真实 HTTP 数据响应 vs 白名单/外网/metadata + UDP 响应内容
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

NAME = "expj88"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

PROBE = r"""
import importlib.util, base64, subprocess, socket

def raw_http(ip, port, path="/", timeout=6, host=None):
    # send real HTTP request, return first bytes or error
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        h = host or ip
        req = f"GET {path} HTTP/1.0\r\nHost: {h}\r\n\r\n"
        s.sendall(req.encode())
        data = b""
        try:
            while len(data) < 400:
                chunk = s.recv(400 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        return ("OK len=%d " % len(data)) + repr(data[:120])
    except socket.timeout:
        return "TIMEOUT"
    except ConnectionResetError:
        return "RST"
    except OSError as e:
        return f"ERR({e.errno})"

print("== [1] shell 数据面测试 ==", flush=True)
print("  httpbin(白名单)  :", raw_http("34.230.248.113", 80, host="httpbin.org"), flush=True)
print("  8.8.8.8          :", raw_http("8.8.8.8", 80), flush=True)
print("  metadata         :", raw_http("169.254.169.254", 80, path="/latest/meta-data/"), flush=True)
print("  172.31.0.2:80    :", raw_http("172.31.0.2", 80), flush=True)
print("  172.31.0.2:22    :", raw_http("172.31.0.2", 22), flush=True)

print("== [2] spawn 数据面测试 ==", flush=True)
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)
ib.patch_sigcheck()

probe_sh = r'''
echo '--- shell 数据面 (spawn 内 python) ---'
python3 - <<'PYEOF'
import socket
def raw_http(ip, port, path="/", timeout=6, host=None):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        h = host or ip
        s.sendall(f"GET {path} HTTP/1.0\r\nHost: {h}\r\n\r\n".encode())
        data = b""
        try:
            while len(data) < 400:
                chunk = s.recv(400 - len(data))
                if not chunk: break
                data += chunk
        except socket.timeout: pass
        s.close()
        return f"OK len={len(data)} " + repr(data[:120])
    except socket.timeout: return "TIMEOUT"
    except ConnectionResetError: return "RST"
    except OSError as e: return f"ERR({e.errno})"

print("  httpbin(白名单):", raw_http("34.230.248.113", 80, host="httpbin.org"), flush=True)
print("  8.8.8.8        :", raw_http("8.8.8.8", 80), flush=True)
print("  metadata       :", raw_http("169.254.169.254", 80, path="/latest/meta-data/"), flush=True)
print("  172.31.0.2:80  :", raw_http("172.31.0.2", 80), flush=True)
print("  172.31.0.2:22  :", raw_http("172.31.0.2", 22), flush=True)
PYEOF
echo '--- udp 172.31.0.2:53 响应内容 ---'
python3 - <<'PYEOF'
import socket
q = bytes.fromhex("aabb01000001000000000000037677770874657374" + "03" + "636f6d0000010001")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(3)
s.sendto(q, ("172.31.0.2", 53))
try:
    d, _ = s.recvfrom(512)
    print("RESP", len(d), d.hex(), flush=True)
except socket.timeout:
    print("TIMEOUT", flush=True)
s.close()
PYEOF
'''
ib.spawn("sh", args=["-c", probe_sh], timeout=90)
"""
run_cmd(sid, PROBE, "data-acl", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
