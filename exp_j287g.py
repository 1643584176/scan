# -*- coding: utf-8 -*-
"""实验J287g: 定位上传 0 字节问题 - 引号/base64/链式写 对比"""
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

NAME = "expj287g"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

DATA = b"print('HELLO_FROM_FILE', flush=True)\n"
B64 = base64.b64encode(DATA).decode()
print("B64:", B64, flush=True)

tests = [
    ("T1_sq_b64", "import base64;open('/tmp/t1.py','w').write(base64.b64decode('%s'))" % B64),
    ("T2_dq_b64", 'import base64;open("/tmp/t2.py","w").write(base64.b64decode("%s"))' % B64),
    ("T3_sq_raw", "open('/tmp/t3.py','w').write('print(1)')"),
    ("T4_dq_raw", 'open("/tmp/t4.py","w").write("print(1)")'),
    ("T5_b64_ret", "import base64;d=base64.b64decode('%s');f=open('/tmp/t5.py','w');n=f.write(d);f.close();print('RET',n,len(d))" % B64),
]
for name, code in tests:
    out = run_cmd(sid, code, name, timeout=100)
    print("%s -> %r" % (name, out[:200]), flush=True)

out = run_cmd(sid, r'''
import os
for p in ("/tmp/t1.py","/tmp/t2.py","/tmp/t3.py","/tmp/t4.py","/tmp/t5.py"):
    if os.path.exists(p):
        print(p, os.path.getsize(p), repr(open(p,"rb").read()[:40]), flush=True)
    else:
        print(p, "MISSING", flush=True)
''', "CHECK_ALL", timeout=100)
print("CHECK_ALL:", repr(out[:600]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
