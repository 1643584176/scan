# -*- coding: utf-8 -*-
"""实验J287j: 原样执行 J287 part0 code, 打印 stdout+stderr"""
import json, time, urllib.request, urllib.error, sys, base64, re
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

NAME = "expj287j"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 从 exp_j287.py 提取 PAYLOAD 并生成与 upload_file 完全相同的 part0 code
src = open('exp_j287.py', encoding='utf-8').read()
m = re.search(r'PAYLOAD = r\'\'\'(.*?)\'\'\'', src, re.S)
payload = m.group(1).encode()
b64 = base64.b64encode(payload).decode()
part0 = b64[0:3500]
code0 = "import base64;open(%r,%r).write(base64.b64decode(%r))" % ("/tmp/rec.py", "wb", part0)
print("part0 code len:", len(code0), flush=True)

out = run_cmd(sid, code0, "PART0_EXACT", timeout=100)
print("PART0_EXACT out:", repr(out[:800]), flush=True)

out = run_cmd(sid, r'''
import os
print("rec.py:", os.path.getsize("/tmp/rec.py") if os.path.exists("/tmp/rec.py") else "MISSING", flush=True)
if os.path.exists("/tmp/rec.py"):
    print("head:", repr(open("/tmp/rec.py","rb").read()[:80]), flush=True)
''', "CHECK", timeout=100)
print("CHECK:", repr(out[:400]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
