# 实验J234: 侦察 init.sock 连接机制 + sandbox进程树 + 30001路由字符串
# 核心: 找 sandbox-runner 是否持有 init.sock 连接 fd (SCM_RIGHTS/继承绕过 SO_PEERCRED)
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

NAME = "expj234"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 进程树 + fd 侦察
CODE_A = r'''
import os, subprocess
out = open("/tmp/d234a.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

# 1) 进程树
r = subprocess.run(["ps", "auxww"], capture_output=True, text=True)
p("PS", r.stdout[:3000])

# 2) 我们自己的 fd (找继承的 socket)
p("SELF_FD", os.listdir("/proc/self/fd"))
for f in os.listdir("/proc/self/fd"):
    try:
        tgt = os.readlink("/proc/self/fd/" + f)
        p("FD", f, tgt)
    except Exception:
        pass

# 3) /proc/net/unix 里的 init.sock
u = open("/proc/net/unix").read()
p("UNIX", u[:2000])

# 4) PID1 的 fd 里的 unix socket
try:
    p("PID1_FD", os.listdir("/proc/1/fd"))
    for f in os.listdir("/proc/1/fd"):
        try:
            tgt = os.readlink("/proc/1/fd/" + f)
            if "socket" in tgt:
                p("P1FD", f, tgt)
        except Exception:
            pass
except Exception as e:
    p("P1FD_ERR", repr(e))

# 5) cmdline 完整
try:
    p("CMDLINE", open("/proc/1/cmdline","rb").read().replace(b"\x00", b" | "))
except Exception as e:
    p("CMDLINE_ERR", repr(e))
p("doneA")
out.close()
'''
run_cmd(sid, CODE_A, "A_RECON", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d234a.txt", "OUT_A", 25000)

# B) dump "/" 开头短字符串 (mux pattern) + 30001 相关 flag 名
CODE_B = r'''
import re
data = open("/tmp/si", "rb").read()
out = open("/tmp/d234b.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

seen = set()
for m in re.finditer(rb"[\x20-\x7e]{4,80}", data):
    s = m.group()
    if s.startswith(b"/") and b"//" not in s[:4]:
        if s not in seen:
            seen.add(s)
            p("PATH", repr(s.decode(errors="replace")))
# flag 名
for pat in (b"--socket", b"--port", b"--addr", b"--http", b"--listen", b"--pubkey", b"--grpc", b"--rpc"):
    i = data.find(pat)
    if i >= 0:
        ctx = data[max(0,i-16):i+48]
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        p("FLAG", pat.decode(), repr(s))
p("doneB")
out.close()
'''
run_cmd(sid, CODE_B, "B_STR", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d234b.txt", "OUT_B", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
