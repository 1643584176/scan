# 实验J151: sandbox-init进程身份 + init.sock监听者 + sandbox-init二进制字符串提取
# j150: /run/vercel/share 含 sandbox-init(16MB可执行) + init.sock(UNIX socket)
#       share非跨沙箱共享; 宿主端口扫描触发杀进程(禁TCP探测宿主)
# 方法: cmdA /proc检查PID1+unix socket监听者; cmdB strings sandbox-init提取协议线索
# 零破坏: 纯读+进程检查, 不连接init.sock不写文件
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
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
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
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

def catfile(sid, path, label, n=15000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj151"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# cmdA: 进程身份 + unix socket
CA = r'''
import os, subprocess
out = open("/tmp/d151a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== PS ===")
p(sh("ps auxww 2>&1 | head -30"))
p("=== PROC1_EXE ===")
p(sh("readlink -f /proc/1/exe 2>&1; readlink -f /proc/1/cwd 2>&1; cat /proc/1/cmdline 2>&1 | tr '\\0' ' '"))
p("=== PROC1_STATUS ===")
p(sh("head -30 /proc/1/status 2>&1"))
p("=== ALL_PROC ===")
for pid in sorted(os.listdir("/proc")):
    if not pid.isdigit():
        continue
    try:
        exe = os.readlink(f"/proc/{pid}/exe")
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\\0", b" ").decode("latin1", "replace")[:100]
        p(pid, exe, "|", cmd)
    except Exception:
        pass
p("=== UNIX_SOCKETS ===")
p(sh("cat /proc/net/unix 2>&1 | head -30"))
p("=== SOCK_STAT ===")
p(sh("ls -la /run/vercel/share/ 2>&1"))
p("=== STAT_INIT ===")
p(sh("stat /run/vercel/share/sandbox-init 2>&1"))
p("=== CGROUP ===")
p(sh("cat /proc/self/cgroup 2>&1; cat /proc/1/cgroup 2>&1"))
p("=== DONE")
out.close()
'''

# cmdB: sandbox-init strings 提取 (分批)
CB = r'''
import re
out = open("/tmp/d151b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
data = open("/run/vercel/share/sandbox-init", "rb").read()
p("size", len(data))
# 提取可打印字符串(>=6)
strs = re.findall(rb"[\x20-\x7e]{6,}", data)
p("str_count", len(strs))
seen = set()
interesting = []
for s in strs:
    try:
        t = s.decode()
    except Exception:
        continue
    if t in seen:
        continue
    seen.add(t)
    tl = t.lower()
    if any(k in tl for k in ["http", "api", "socket", "token", "secret", "key", "auth", "passwd",
                             "credential", "sandbox", "vercel", "oidc", "jwt", "bearer", "password",
                             "cookie", "session", "tls", "cert", "pem", "sign", "cmd", "exec",
                             "proxy", "forward", "websock", "grpc", "unix", "sock", "pid", "host",
                             "mount", "chroot", "namespace", "netlink", "cap_", "seccomp", "ptrace",
                             "ioctl", "loop", "vda", "vdb", "block", "xfs", "volume", "share"]):
        interesting.append(t)
p("=== INTERESTING ===")
for t in interesting[:400]:
    p("I:", t[:160])
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "proc-id", timeout=120)
catfile(sid, "/tmp/d151a.txt", "d151a", 8000)

run_cmd(sid, CB, "init-strings", timeout=250)
catfile(sid, "/tmp/d151b.txt", "d151b", 14000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
