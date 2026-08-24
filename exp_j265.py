# -*- coding: utf-8 -*-
"""实验J265: 精确测量沙箱 TTL
cmd 内每 5 秒打印时间戳; 宿主侧每 15 秒 GET sandbox 状态
目标: 确定沙箱被杀的时间点/机制 (TTL vs 操作触发)
"""
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
    out = ""
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
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    if out:
        print(out, flush=True)
    return out

NAME = "expj265"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
data = json.loads(r)
sid = data["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)
print("create resp keys:", sorted(data["sandbox"].keys()), flush=True)
t0 = time.time()

# 每 5 秒打印时间戳, 共 90 秒
CODE_1 = r'''
import time
t0 = time.time()
for i in range(18):
    print("TICK", i, "t=%.1f" % (time.time() - t0), flush=True)
    time.sleep(5)
print("DONE_1 alive 90s", flush=True)
'''
# 后台? 不, 前台但宿主侧同时轮询
import threading

stop = threading.Event()
def poll():
    while not stop.is_set():
        c, r = api("GET", f"/v2/sandboxes/{NAME}?teamId={TEAM}")
        try:
            d = json.loads(r)
            s = d.get("sandbox", {})
            print("POLL t=%.0f status=%s state=%s" % (time.time()-t0,
                  s.get("status"), s.get("state")), flush=True)
        except Exception as e:
            print("POLL t=%.0f raw %s %.200s" % (time.time()-t0, c, r), flush=True)
        time.sleep(10)

th = threading.Thread(target=poll, daemon=True)
th.start()
r1 = run_cmd(sid, CODE_1, "T1_TTL", timeout=200)
stop.set()

# 复查沙箱状态
c, r = api("GET", f"/v2/sandboxes/{NAME}?teamId={TEAM}")
print("final get:", c, r[:400], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
