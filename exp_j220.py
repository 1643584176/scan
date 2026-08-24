# 实验J220: 提取二进制中的 connect-go 路由字符串 + 请求探测有效路径
# connect-go 路由格式: /pkg.Service/Method
# 1) 状态机提取字符串 过滤含 vercel/.Service/含"/"的路由
# 2) 多种请求探测路径响应差异
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
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

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj220"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si && ls -la /tmp/si", "CP", 2000)

# 1) 字符串提取 (状态机, 无OOM)
CODE = r'''
data = open("/tmp/si", "rb").read()
out = open("/tmp/d220.txt", "w")
def p(s):
    out.write(s + "\n"); out.flush()
    print(s, flush=True)

# 状态机提取字符串
s = []
total = 0
for b in data:
    if 0x20 <= b < 0x7f:
        s.append(b)
    else:
        if len(s) >= 6:
            total += 1
            st = bytes(s)
            # 过滤: 含"/" 或含vercel/Service/Method/RPC/sign/key 关键字
            low = st.lower()
            if (b"/" in st and b"/" in st[1:]) or b"vercel" in low or b"service" in low \
               or b"method" in low or b"signature" in low or b"ed25519" in low or b"connect" in low:
                if len(st) < 300:
                    p("STR " + st.decode("latin1"))
        s = []
p("TOTAL_STRINGS", total)
out.close()
'''
st = run_cmd(sid, CODE, "J220A", timeout=200)
time.sleep(1)
bashfile(sid, "grep -a -E '^STR' /tmp/d220.txt | head -80", "STRS", 20000)

# 2) 路由探测 (多个路径/方法, 看响应码差异)
REQCODE = r'''
import urllib.request, urllib.error, sys
def probe(method, path, headers=None, body=None):
    try:
        req = urllib.request.Request("http://127.0.0.1:30001" + path, method=method, headers=headers or {})
        if body:
            req.data = body
        try:
            r = urllib.request.urlopen(req, timeout=4)
            print("OK", method, path, r.status, r.read(120), flush=True)
        except urllib.error.HTTPError as e:
            print("HE", method, path, e.code, e.read(160), flush=True)
    except Exception as e:
        print("EX", method, path, type(e).__name__, str(e)[:80], flush=True)

paths = ["/", "/health", "/api", "/api/v1", "/v1", "/version", "/vercel", "/sandbox",
         "/vercel.sandbox.SandboxService/Exec", "/vercel.sandbox.v1.SandboxService/Exec",
         "/vercel.api.v1.SandboxService/Exec", "/sandbox.SandboxService/Exec",
         "/vercel.sandbox.v1.Sandbox/Exec", "/vercel.sandbox.Sandbox/Exec",
         "/grpc.health.v1.Health/Check", "/grpc.health.v1.Health/Status"]
for p in paths:
    probe("POST", p, {"Content-Type": "application/connect+proto"})
probe("GET", "/")
probe("OPTIONS", "/")
'''
st = run_cmd(sid, REQCODE, "J220B", timeout=200)
time.sleep(1)
bashfile(sid, "true", "NOOP", 500)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
