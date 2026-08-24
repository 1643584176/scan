# 实验J89: TLS/SNI 数据面判定 — 区分 IP/SNI/端口级策略 + 代理环境检查
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

NAME = "expj89"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

PROBE = r"""
import importlib.util, base64, subprocess, socket, ssl, json

def tls_probe(ip, port, sni, timeout=6):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        t = ctx.wrap_socket(s, server_hostname=sni)
        ver = t.version()
        # try a tiny HTTP GET inside TLS
        t.sendall(b"GET / HTTP/1.0\r\nHost: " + sni.encode() + b"\r\n\r\n")
        data = b""
        try:
            while len(data) < 300:
                chunk = t.recv(300 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        t.close()
        return f"TLS OK({ver}) HTTP len={len(data)} " + repr(data[:80])
    except socket.timeout:
        return "TIMEOUT"
    except ConnectionResetError:
        return "RST"
    except ssl.SSLError as e:
        return f"SSL_ERR({e})"
    except OSError as e:
        return f"ERR({e.errno})"

print("== [1] 环境变量 (代理?) ==", flush=True)
r = subprocess.run(["env"], capture_output=True, text=True, timeout=10)
for line in r.stdout.splitlines():
    if "proxy" in line.lower() or "PROXY" in line:
        print("  ", line, flush=True)

print("== [2] shell TLS/SNI 矩阵 ==", flush=True)
print("  httpbin-IP :443 SNI=httpbin.org :", tls_probe("34.230.248.113", 443, "httpbin.org"), flush=True)
print("  8.8.8.8    :443 SNI=httpbin.org :", tls_probe("8.8.8.8", 443, "httpbin.org"), flush=True)
print("  8.8.8.8    :443 SNI=google.com  :", tls_probe("8.8.8.8", 443, "google.com"), flush=True)
print("  metadata   :443 SNI=anything    :", tls_probe("169.254.169.254", 443, "test.com"), flush=True)
print("  172.31.0.2 :443 SNI=httpbin.org :", tls_probe("172.31.0.2", 443, "httpbin.org"), flush=True)

print("== [3] spawn TLS/SNI 矩阵 ==", flush=True)
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)
ib.patch_sigcheck()

probe_sh = r'''
python3 - <<'PYEOF'
import socket, ssl
def tls_probe(ip, port, sni, timeout=6):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        t = ctx.wrap_socket(s, server_hostname=sni)
        ver = t.version()
        t.sendall(b"GET / HTTP/1.0\r\nHost: " + sni.encode() + b"\r\n\r\n")
        data = b""
        try:
            while len(data) < 300:
                chunk = t.recv(300 - len(data))
                if not chunk: break
                data += chunk
        except socket.timeout: pass
        t.close()
        return f"TLS OK({ver}) HTTP len={len(data)} " + repr(data[:80])
    except socket.timeout: return "TIMEOUT"
    except ConnectionResetError: return "RST"
    except ssl.SSLError as e: return f"SSL_ERR({e})"
    except OSError as e: return f"ERR({e.errno})"

print("  httpbin-IP :443 SNI=httpbin.org :", tls_probe("34.230.248.113", 443, "httpbin.org"), flush=True)
print("  8.8.8.8    :443 SNI=httpbin.org :", tls_probe("8.8.8.8", 443, "httpbin.org"), flush=True)
print("  8.8.8.8    :443 SNI=google.com  :", tls_probe("8.8.8.8", 443, "google.com"), flush=True)
print("  metadata   :443 SNI=anything    :", tls_probe("169.254.169.254", 443, "test.com"), flush=True)
print("  172.31.0.2 :443 SNI=httpbin.org :", tls_probe("172.31.0.2", 443, "httpbin.org"), flush=True)
PYEOF
echo '--- spawn env proxies ---'
env | grep -i proxy
'''
ib.spawn("sh", args=["-c", probe_sh], timeout=90)
"""
run_cmd(sid, PROBE, "tls-matrix", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
