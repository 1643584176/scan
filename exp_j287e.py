# -*- coding: utf-8 -*-
"""实验J287e: 诊断 - 直接执行 /tmp/rec.py 并检查文件"""
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

def upload_file(sid, remote_path, data_bytes):
    b64 = base64.b64encode(data_bytes).decode()
    CHUNK = 3500
    for i in range(0, len(b64), CHUNK):
        part = b64[i:i + CHUNK]
        mode = "w" if i == 0 else "a"
        code = "import base64;open(%r,%r).write(base64.b64decode(%r))" % (remote_path, mode, part)
        r = run_cmd(sid, code, "UPLOAD_%d" % (i // CHUNK), timeout=100)
        if "DEAD" in (r or ""):
            return False
    return True

NAME = "expj287e"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 简单测试文件
TEST = b"print('HELLO_FROM_FILE', flush=True)\n"
ok = upload_file(sid, "/tmp/t1.py", TEST)
print("upload t1:", ok, flush=True)

# 检查文件 + 执行
out = run_cmd(sid, r'''
import os
print("t1 size:", os.path.getsize("/tmp/t1.py"), flush=True)
print(repr(open("/tmp/t1.py","rb").read()), flush=True)
''', "CHECK_T1", timeout=100)
print("CHECK:", repr(out[:400]), flush=True)

out = run_cmd(sid, "exec(open('/tmp/t1.py').read())", "EXEC_T1", timeout=100)
print("EXEC_T1:", repr(out[:400]), flush=True)

out = run_cmd(sid, "import subprocess; subprocess.run(['python3','/tmp/t1.py'])", "SUB_T1", timeout=100)
print("SUB_T1:", repr(out[:400]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
