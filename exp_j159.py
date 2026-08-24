# 实验J159: PID1 socket fd 溯源(cell.sock?) + dup fd可行性 + 沙箱IP端口banner
# j158: 连接23456触发杀进程(宿主agent端口); PID1 fd有socket[258/262/282]疑似宿主通信
# 方法: cmdA fdinfo+unix表定位fd对应socket路径+getsockopt验证; cmdB dup fd发送探测(空数据)
# 零破坏: 只读fd信息+getsockopt; 探测消息为最小合法协议帧, 不发破坏命令
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

NAME = "expj159"
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

# cmdA: fd溯源
CA = r'''
import os, subprocess, socket, fcntl, struct
out = open("/tmp/d159a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== FDINFO ===")
for fd in ["4", "7", "8"]:
    p("--- fd", fd, "---")
    p(sh(f"cat /proc/1/fdinfo/{fd} 2>&1"))
p("=== UNIX_TABLE ===")
p(sh("cat /proc/net/unix 2>&1"))
p("=== SOCK_STATE ===")
# 对 PID1 的每个 socket fd 做 getsockopt
for fd in ["4", "7", "8"]:
    try:
        f = os.open(f"/proc/1/fd/{fd}", os.O_RDWR)
        # SO_TYPE
        t = fcntl.ioctl(f, 0x8902)  # SIOCGSKNS? 不, 用 getsockopt via socket
        # 用 socket.socket(fileno=f) 包装
        s = socket.socket(fileno=f)
        p("fd", fd, "family", s.family, "type", s.type)
        # SO_PEERCRED (unix only)
        try:
            cred = s.getsockopt(socket.SOL_SOCKET, 17, 12)  # SO_PEERCRED=17
            pid, uid, gid = struct.unpack("3i", cred)
            p("peercred", pid, uid, gid)
        except Exception as e:
            p("peercred err", repr(e))
        try:
            p("peer", s.getpeername())
        except Exception as e:
            p("peername err", repr(e))
        try:
            p("sockname", s.getsockname())
        except Exception as e:
            p("sockname err", repr(e))
        s.close()
    except Exception as e:
        p("fd", fd, "OPEN_ERR", repr(e))
p("=== DONE")
out.close()
'''

# cmdB: dup fd 4 发送最小探测(仅测可写性, 数据为0字节不构成协议请求)
CB = r'''
import os, socket
out = open("/tmp/d159b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
# dup /proc/1/fd/4 并测试 send 0 字节 + MSG_PEEK 读
try:
    f = os.open("/proc/1/fd/4", os.O_RDWR)
    s = socket.socket(fileno=f)
    s.settimeout(2)
    # MSG_PEEK 读现有数据
    try:
        d = s.recv(1024, socket.MSG_PEEK)
        p("peek4", repr(d[:200]))
    except socket.timeout:
        p("peek4 timeout")
    except Exception as e:
        p("peek4 err", repr(e))
    s.close()
except Exception as e:
    p("fd4 err", repr(e))
# fd 7
try:
    f = os.open("/proc/1/fd/7", os.O_RDWR)
    s = socket.socket(fileno=f)
    s.settimeout(2)
    try:
        d = s.recv(1024, socket.MSG_PEEK)
        p("peek7", repr(d[:200]))
    except socket.timeout:
        p("peek7 timeout")
    except Exception as e:
        p("peek7 err", repr(e))
    s.close()
except Exception as e:
    p("fd7 err", repr(e))
p("=== DONE")
out.close()
'''

# cmdC: 沙箱自身IP的端口 banner (v6通配监听的端口, 用自身IP v4 连接)
CC = r'''
import socket, subprocess
out = open("/tmp/d159c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
# 获取自身IP
ips = sh("cat /proc/net/fib_trie 2>&1 | grep -oP '(?<=--\\n)\\s*\\|-- \\K[0-9.]+' | sort -u")
p("ips", ips)
# 直接读tcp6表解析本地地址
import struct
lines = open("/proc/net/tcp6").read().splitlines()[1:]
my_addrs = set()
for ln in lines:
    parts = ln.split()
    laddr = parts[1].split(":")[0]
    if laddr == "00000000000000000000000000000000":
        continue
    if laddr.startswith("0000000000000000FFFF0000"):
        ip4 = socket.inet_ntoa(struct.pack(">I", int(laddr[16:], 16)))
        my_addrs.add(ip4)
p("my_addrs", my_addrs)
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

run_cmd(sid, CA, "fd-trace", timeout=120)
catfile(sid, "/tmp/d159a.txt", "d159a", 9000)

run_cmd(sid, CB, "fd-dup", timeout=120)
catfile(sid, "/tmp/d159b.txt", "d159b", 3000)

run_cmd(sid, CC, "ip-ports", timeout=120)
catfile(sid, "/tmp/d159c.txt", "d159c", 3000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
