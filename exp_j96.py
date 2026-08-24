# 实验J96: sandbox-init 二进制分析 — 端口/路由/敏感字符串上下文
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

NAME = "expj96"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import re, os

BIN = "/proc/1/root/run/vercel/share/sandbox-init"
data = open(BIN, "rb").read()
print(f"size={len(data)}", flush=True)

def strings_around(needle, radius=180, max_hits=8):
    hits = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        window = data[max(0, i-radius):i+radius]
        # 提取可打印串
        strs = re.findall(rb"[ -~]{4,}", window)
        hits.append((i, [s.decode(errors="replace") for s in strs][:14]))
        start = i + 1
        if len(hits) >= max_hits:
            break
    return hits

for needle in [b"30001", b"30002", b"23456", b"404 page not found"]:
    print(f"== needle {needle} ==", flush=True)
    for off, strs in strings_around(needle):
        print(f"  @{off}: {strs}", flush=True)

print("== http 路径字符串 ==", flush=True)
paths = set()
for m in re.finditer(rb"/(?:vercel|cell|sandbox|session|v\d|api)[a-zA-Z0-9_./{}-]{3,60}", data):
    s = m.group().decode(errors="replace")
    paths.add(s)
for p in sorted(paths)[:60]:
    print("  ", p, flush=True)

print("== 端口字符串 ==", flush=True)
ports = set()
for m in re.finditer(rb":\d{4,5}\b", data):
    ports.add(m.group().decode())
print("  ", sorted(ports)[:40], flush=True)
"""
run_cmd(sid, PROBE, "bin-analysis", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
