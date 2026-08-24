# -*- coding: utf-8 -*-
"""实验J269: 1 秒限制边界 + 后台进程存活测试
A: 0.5s CPU (应成功)
B: 0.95s CPU (边界)
C: setsid nohup 后台 sleep 25 + touch /tmp/OK_BG; 命令立即退出
D: 25s 后检查 /tmp/OK_BG (后台进程是否存活)
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

NAME = "expj269"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: 0.5s CPU
rA = run_cmd(sid, 'import time; t0=time.time();\n'
                   'while time.time()-t0 < 0.5: pass\n'
                   'print("OK_A")', "A_CPU05", timeout=100)
print("A done:", "OK_A" in (rA or ""), flush=True)

# B: 0.95s CPU (边界)
rB = run_cmd(sid, 'import time; t0=time.time();\n'
                   'while time.time()-t0 < 0.95: pass\n'
                   'print("OK_B")', "B_CPU095", timeout=100)
print("B done:", "OK_B" in (rB or ""), flush=True)

# C: setsid nohup 后台任务, 命令立即退出
CODE_C = r'''
import subprocess, os, time
# 写一个后台脚本
open("/tmp/bg_task.py", "w").write(
    "import time\n"
    "time.sleep(25)\n"
    "open('/tmp/OK_BG', 'w').write('yes')\n"
)
# setsid + nohup + 重定向, 完全脱离
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/bg_task.py"],
    stdout=open("/tmp/bg.out", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, start_new_session=True,
    close_fds=True,
)
print("spawned pid", r.pid, flush=True)
time.sleep(0.3)
print("OK_C", flush=True)
'''
rC = run_cmd(sid, CODE_C, "C_BG", timeout=100)
print("C done:", "OK_C" in (rC or ""), flush=True)

# D: 25 秒后检查 (宿主侧等待)
time.sleep(27)
CODE_D = r'''
import os
print("bg_file_exists:", os.path.exists("/tmp/OK_BG"), flush=True)
try:
    print("bg_out:", open("/tmp/bg.out").read()[:200], flush=True)
except Exception as e:
    print("bg_out_err", repr(e)[:100], flush=True)
import subprocess
r = subprocess.run("ps -eo pid,ppid,stat,etime,cmd | head -20", shell=True,
                   capture_output=True, timeout=8)
print((r.stdout or b"").decode("latin1", "replace"), flush=True)
print("OK_D", flush=True)
'''
rD = run_cmd(sid, CODE_D, "D_CHECK", timeout=100)
print("D done:", "OK_D" in (rD or ""), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
