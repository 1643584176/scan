# -*- coding: utf-8 -*-
"""实验J260: 分块下载 sandbox-init 到本地 (base64 分块)
目标: 9MB 二进制分 24 块取回, 本地完整分析 (capstone/gopclntab)
"""
import json, time, urllib.request, urllib.error, sys, base64, os
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
    out = []
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out.append(d.get("data", ""))
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            out.append(line[:2000])
    return "\n".join(out)

NAME = "expj260"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) buildinfo 版本确认
CODE_A = r'''
d = open("/run/vercel/share/sandbox-init", "rb").read()
bi = d.find(b"\xff Go buildinf:")
print("BI", hex(bi), flush=True)
seg = d[bi:bi+256]
asc = "".join(chr(b) if 32 <= b < 127 else "." for b in seg)
print(asc[:240], flush=True)
'''
out = run_cmd(sid, CODE_A, "A_BUILDINFO", timeout=100)
print("OUT_A:", out[:500], flush=True)

# B) 分块下载: 每块 400KB, 24 块
CHUNK = 400 * 1024
TOTAL = 9134264
f = open("_sandbox_init_new.bin", "wb")
ok = 0
for i in range((TOTAL + CHUNK - 1) // CHUNK):
    start = i * CHUNK
    end = min(start + CHUNK, TOTAL)
    CODE = f'''
import base64
d = open("/run/vercel/share/sandbox-init", "rb").read()
b = d[{start}:{end}]
print(base64.b64encode(b).decode(), flush=True)
'''
    out = run_cmd(sid, CODE, f"DL{i}", timeout=100)
    if not out:
        print(f"  DL{i} EMPTY", flush=True)
        continue
    try:
        f.write(base64.b64decode(out.strip()))
        ok += 1
        print(f"  DL{i} ok {end-start}B", flush=True)
    except Exception as e:
        print(f"  DL{i} DECODE_ERR {str(e)[:100]}", flush=True)
f.close()
print(f"downloaded {ok}/{ (TOTAL+CHUNK-1)//CHUNK } chunks", flush=True)
print("size:", os.path.getsize("_sandbox_init_new.bin"), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
