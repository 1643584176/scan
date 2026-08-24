# -*- coding: utf-8 -*-
"""实验J266: 区分 cmd 命令超时 vs 沙箱 TTL
A: sleep 3 + echo (预期成功)
B: sleep 15 + echo (观察是否被杀)
C: echo (B 被杀后沙箱是否还活着?)
D: sleep 30 分秒打印 (精确超时点)
打印 create resp 完整字段 (timeout/persistent/status)
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
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    dt = time.time() - t0
    print(f"=== cmd[{label}] status {c} wall={dt:.1f}s ===", flush=True)
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

NAME = "expj266"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
data = json.loads(r)["sandbox"]
sid = data["currentSessionId"]
print("sid:", sid, flush=True)
for k in ("timeout", "status", "persistent", "memory", "vcpus", "runtime", "region"):
    print("  %s = %r" % (k, data.get(k)), flush=True)

rA = run_cmd(sid, 'import time; time.sleep(3); print("OK_A")', "A_SLEEP3", timeout=100)
print("A done:", "OK_A" in (rA or ""), flush=True)

rB = run_cmd(sid, 'import time; time.sleep(15); print("OK_B")', "B_SLEEP15", timeout=100)
print("B done:", "OK_B" in (rB or ""), flush=True)

rC = run_cmd(sid, 'print("OK_C")', "C_ECHO", timeout=100)
print("C done:", "OK_C" in (rC or ""), flush=True)

if "OK_C" in (rC or ""):
    CODE_D = r'''
import time
t0 = time.time()
for i in range(12):
    print("T%d t=%.1f" % (i, time.time() - t0), flush=True)
    time.sleep(2)
print("OK_D", flush=True)
'''
    rD = run_cmd(sid, CODE_D, "D_SLEEP24", timeout=100)
    print("D done:", "OK_D" in (rD or ""), flush=True)
    rE = run_cmd(sid, 'print("OK_E")', "E_ECHO", timeout=100)
    print("E done:", "OK_E" in (rE or ""), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
