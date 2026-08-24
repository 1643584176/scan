# -*- coding: utf-8 -*-
"""实验J287f: 诊断文件写入 0 字节问题
1) shell echo 同命令写读  2) 跨命令读  3) python write 返回值 + 同进程读回
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
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
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("EXIT:", json.dumps(d.get("command", {}))[:300], flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

NAME = "expj287f"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 1) shell 同命令写读
out = run_cmd(sid, r'''
import subprocess
r = subprocess.run("echo hello123 > /tmp/x1 && cat /tmp/x1 && ls -la /tmp/x1", shell=True, capture_output=True, timeout=6)
print("RC:", r.returncode, flush=True)
print("OUT:", (r.stdout or b"").decode("latin1", "replace"), flush=True)
print("ERR:", (r.stderr or b"").decode("latin1", "replace"), flush=True)
''', "SHELL_WRITE", timeout=100)
print("SHELL_WRITE:", repr(out[:400]), flush=True)

# 2) 跨命令读
out = run_cmd(sid, r'''
import subprocess
r = subprocess.run("cat /tmp/x1 2>&1; ls -la /tmp/x1 2>&1", shell=True, capture_output=True, timeout=6)
print("OUT:", (r.stdout or b"").decode("latin1", "replace"), flush=True)
''', "CROSS_READ", timeout=100)
print("CROSS_READ:", repr(out[:400]), flush=True)

# 3) python 同进程写+读+打印返回值
out = run_cmd(sid, r'''
f = open("/tmp/x2", "w")
n = f.write("PYDATA_789")
f.flush()
f.close()
print("write returned:", n, flush=True)
print("readback:", repr(open("/tmp/x2","rb").read()), flush=True)
import os
print("size:", os.path.getsize("/tmp/x2"), flush=True)
''', "PY_WRITE", timeout=100)
print("PY_WRITE:", repr(out[:400]), flush=True)

# 4) 跨命令读 x2
out = run_cmd(sid, r'''
import os
print("x2 exists:", os.path.exists("/tmp/x2"), flush=True)
if os.path.exists("/tmp/x2"):
    print("x2 size:", os.path.getsize("/tmp/x2"), flush=True)
    print("x2 content:", repr(open("/tmp/x2","rb").read()), flush=True)
''', "CROSS_X2", timeout=100)
print("CROSS_X2:", repr(out[:400]), flush=True)

# 5) 后台进程写入 (nohup) 跨命令读
out = run_cmd(sid, r'''
import subprocess
open("/tmp/bg.py", "w").write("open('/tmp/bg.txt','w').write('BG_DATA_456')\n")
r = subprocess.Popen(["setsid", "nohup", "python3", "/tmp/bg.py"],
    stdout=open("/tmp/bg.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True)
print("bg pid:", r.pid, flush=True)
''', "BG_START", timeout=100)
print("BG_START:", repr(out[:400]), flush=True)
time.sleep(3)
out = run_cmd(sid, r'''
import os
print("bg.txt:", os.path.exists("/tmp/bg.txt"), flush=True)
if os.path.exists("/tmp/bg.txt"):
    print("content:", repr(open("/tmp/bg.txt","rb").read()), flush=True)
print("bg.py size:", os.path.getsize("/tmp/bg.py"), flush=True)
''', "BG_READ", timeout=100)
print("BG_READ:", repr(out[:400]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
