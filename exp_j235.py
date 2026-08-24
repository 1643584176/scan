# 实验J235: 找init.sock客户端进程 + sudo测试 + 30001监听确认 + 补dump字符串
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

NAME = "expj235"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si ; ls -la /tmp/si", "PREP", 1000)

# A) 找 init.sock 客户端 + 30001 监听 + sudo 测试
CODE_A = r'''
import os, subprocess
out = open("/tmp/d235a.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

# 1) unix socket 连接详情
u = open("/proc/net/unix").read()
for ln in u.splitlines():
    if "init.sock" in ln or (ln.strip() and ln.split()[6] in ("1327","1360","1359")):
        p("U", ln.strip())

# 2) 每个进程的 fd, 找 init.sock inode
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        for f in os.listdir(f"/proc/{pid}/fd"):
            try:
                tgt = os.readlink(f"/proc/{pid}/fd/{f}")
                if "socket" in tgt:
                    ino = tgt.split("[")[1].rstrip("]")
                    if ino in ("1327", "1360", "1359", "613"):
                        p("FDHIT", pid, f, tgt)
            except Exception:
                pass
    except Exception:
        pass

# 3) /proc/1/net/tcp 找 30001 (0x7531 = 30001)
for f in ("/proc/1/net/tcp", "/proc/1/net/tcp6"):
    try:
        t = open(f).read()
        for ln in t.splitlines()[1:]:
            if ":7531" in ln or ":753" in ln:
                p("TCP", f, ln.strip())
    except Exception as e:
        p("TCP_ERR", f, repr(e))

# 4) sudo 测试
for cmd in ("id", "ls /proc/13/fd", "cat /proc/13/status | head -5"):
    try:
        r = subprocess.run(["sudo", "-n", "bash", "-c", cmd], capture_output=True, text=True, timeout=10)
        p("SUDO", cmd, "rc", r.returncode, (r.stdout + r.stderr)[:300].replace("\n", "|"))
    except Exception as e:
        p("SUDO_ERR", cmd, repr(e))

# 5) root 进程 13/15/16 的 fd
for pid in ("13", "15", "16"):
    try:
        p("ROOTFD", pid, os.listdir(f"/proc/{pid}/fd"))
        for f in os.listdir(f"/proc/{pid}/fd"):
            try:
                tgt = os.readlink(f"/proc/{pid}/fd/{f}")
                if "socket" in tgt:
                    p("ROOTFDS", pid, f, tgt)
            except Exception:
                pass
    except Exception as e:
        p("ROOTFD_ERR", pid, repr(e))
p("doneA")
out.close()
'''
run_cmd(sid, CODE_A, "A_FINDCLIENT", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d235a.txt", "OUT_A", 20000)

# B) dump "/" 开头短字符串 + flag 名 (补做)
CODE_B = r'''
import re
data = open("/tmp/si", "rb").read()
out = open("/tmp/d235b.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

seen = set()
for m in re.finditer(rb"[\x20-\x7e]{4,80}", data):
    s = m.group()
    if s.startswith(b"/") and b"//" not in s[:4] and b"http" not in s:
        if s not in seen:
            seen.add(s)
            p("PATH", repr(s.decode(errors="replace")))
for pat in (b"--socket", b"--port", b"--addr", b"--http", b"--listen", b"--pubkey", b"--grpc", b"--rpc", b"30001", b"127.0.0.1"):
    i = data.find(pat)
    if i >= 0:
        ctx = data[max(0,i-16):i+48]
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        p("FLAG", pat.decode(), hex(i), repr(s))
p("doneB")
out.close()
'''
run_cmd(sid, CODE_B, "B_STR", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d235b.txt", "OUT_B", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
