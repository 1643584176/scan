# 实验J221: re.finditer 流式提取字符串(不OOM不慢循环) + GET/POST 请求差异确认
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

NAME = "expj221"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si", "CP", 2000)

# 1) finditer 流式提取 (分块, C速度, 无OOM)
CODE = r'''
import re
out = open("/tmp/d221.txt", "w")
def p(s):
    out.write(s + "\n")
    print(s, flush=True)

KEYS = (b"vercel", b"service", b"method", b"signature", b"ed25519", b"connect",
        b"session", b"exec", b"command", b"sandbox", b"rpc", b"proto")
data = open("/tmp/si", "rb").read()
total = 0
for m in re.finditer(rb"[\x20-\x7e]{6,}", data):
    st = m.group()
    total += 1
    low = st.lower()
    if (st.count(b"/") >= 1 and b"." in st) or any(k in low for k in KEYS):
        if 6 <= len(st) <= 250:
            p("STR " + st.decode("latin1"))
p("TOTAL", total)
out.close()
'''
st = run_cmd(sid, CODE, "J221A", timeout=200)
time.sleep(1)
bashfile(sid, "grep -a -E '^STR' /tmp/d221.txt | grep -a -E 'vercel|Service|/.*/' | head -60", "STRS", 25000)
bashfile(sid, "grep -a -c '^STR' /tmp/d221.txt; tail -1 /tmp/d221.txt", "CNT", 2000)

# 2) GET 请求差异 (确认 GET 幸存)
CODE2 = r'''
import urllib.request, urllib.error
for path in ["/", "/health", "/x/y", "/vercel.sandbox.v1.SandboxService/Exec"]:
    try:
        r = urllib.request.urlopen("http://127.0.0.1:30001" + path, timeout=4)
        print("OK", path, r.status, r.read(100), flush=True)
    except urllib.error.HTTPError as e:
        print("HE", path, e.code, e.read(150), flush=True)
    except Exception as e:
        print("EX", path, type(e).__name__, str(e)[:80], flush=True)
print("GET_DONE", flush=True)
'''
st = run_cmd(sid, CODE2, "J221B", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
