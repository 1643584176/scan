# 实验J225: 读 /proc/1/cmdline + environ + 扫描 argv 区域找 pub key
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
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj225"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 读 cmdline/environ + 扫 argv 区
CODE = r'''
import os
out = open("/tmp/d225.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

try:
    cl = open("/proc/1/cmdline", "rb").read()
    p("CMDLINE_BYTES", len(cl), cl.hex())
    parts = cl.split(b"\x00")
    for i, s in enumerate(parts):
        if s:
            p("ARG", i, s.decode("latin1"))
except Exception as e:
    p("CMDLINE_ERR", repr(e))

try:
    env = open("/proc/1/environ", "rb").read()
    p("ENVIRON_BYTES", len(env))
    for s in env.split(b"\x00"):
        if s:
            t = s.decode("latin1")
            if any(k in t.lower() for k in ["key", "sign", "secret", "token", "auth", "sandbox", "session", "vercel"]):
                p("ENV", t)
except Exception as e:
    p("ENVIRON_ERR", repr(e))

# 读 argv 内存区 (maps 里 [stack] 或进程参数区)
try:
    maps = open("/proc/1/maps").read()
    for ln in maps.splitlines():
        if "[stack]" in ln or "[vdso]" in ln:
            p("MAPS_STACK", ln)
except Exception as e:
    p("MAPS_ERR", repr(e))
p("done")
out.close()
'''
st = run_cmd(sid, CODE, "J225", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d225.txt", "READOUT", 30000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
