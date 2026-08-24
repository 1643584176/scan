# -*- coding: utf-8 -*-
"""实验J267: 命令终止机制精确分析
A: 循环 12 次 print tick + sleep 1 (看命令能活几秒)
B: 纯 CPU 计算 5 秒 (区分 sleep vs 时间)
C: 命令被杀后 ps aux 看进程树
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

NAME = "expj267"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: tick 循环 1 秒间隔
CODE_A = r'''
import time
t0 = time.time()
for i in range(12):
    print("T%d t=%.1f" % (i, time.time() - t0), flush=True)
    time.sleep(1)
print("OK_A", flush=True)
'''
rA = run_cmd(sid, CODE_A, "A_TICK1", timeout=100)
print("A done:", "OK_A" in (rA or ""), flush=True)

# B: 纯 CPU 5 秒
CODE_B = r'''
import time
t0 = time.time()
x = 0
while time.time() - t0 < 5:
    x += 1
    if x % 10000000 == 0:
        print("B t=%.1f" % (time.time() - t0), flush=True)
print("OK_B", flush=True)
'''
rB = run_cmd(sid, CODE_B, "B_CPU", timeout=100)
print("B done:", "OK_B" in (rB or ""), flush=True)

# C: 进程树
CODE_C = r'''
import subprocess
r = subprocess.run("ps -eo pid,ppid,stat,etime,cmd", shell=True, capture_output=True, timeout=10)
print((r.stdout or b"").decode("latin1", "replace"), flush=True)
print("OK_C", flush=True)
'''
rC = run_cmd(sid, CODE_C, "C_PS", timeout=100)
print("C done:", "OK_C" in (rC or ""), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
