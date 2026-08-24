# 实验J158: 本地端口探测(7531/7532/23456) + 重新提取二进制 + gopclntab修正解析
# j157: netns共享视图显示 7531/7532/23456 监听 + 23456->100.64.0.1:44138 ESTABLISHED(宿主控制通道)
# 方法: cmdA 提取; cmdB 本地端口banner探测(沙箱自身IP, 不碰宿主); cmdC gopclntab
# 零破坏: 本地TCP连接(沙箱内), 无数据写入
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

NAME = "expj158"
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

# cmdA: 提取二进制
CA = r'''
import os
out = open("/tmp/d158a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def read_mem(addr, size):
    f = os.open("/proc/1/mem", os.O_RDONLY)
    try:
        os.lseek(f, addr, 0)
        d = os.read(f, size)
        return d
    finally:
        os.close(f)
dst = open("/tmp/sinit.bin", "wb")
total = 0
addr = 0x400000
end = 0x00e9e000
CH = 0x1000
while addr < end:
    d = read_mem(addr, CH)
    if not d:
        p("short_at", hex(addr))
        break
    dst.write(d)
    addr += len(d)
    total += len(d)
dst.close()
p("extracted_total", total)
p("=== DONE")
out.close()
'''

# cmdB: 本地端口 banner 探测 (127.0.0.1 + 自身IP)
CB = r'''
import socket, subprocess
out = open("/tmp/d158b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== SELF_IP ===")
# 从路由表拿自身IP
route = open("/proc/net/route").read().splitlines()
for line in route[1:]:
    parts = line.split()
    if parts[1] == "00000000":
        continue
    p("route_if", parts[0], "dst", parts[1])
p(sh("cat /proc/net/fib_trie 2>&1 | grep -A1 '/32 host' | head -20"))
p("=== TCP_FULL ===")
p(sh("cat /proc/net/tcp 2>&1"))
p(sh("cat /proc/net/tcp6 2>&1"))
p("=== LOCAL_CONNECT ===")
def probe(ip, port, t=2):
    try:
        s = socket.socket(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        s.settimeout(1.5)
        d = b""
        try:
            d = s.recv(512)
        except Exception:
            pass
        s.close()
        return "OPEN recv=" + repr(d[:200])
    except Exception as e:
        return "ERR %r" % (e,)
for ip in ["127.0.0.1", "::1"]:
    for port in [7531, 7532, 23456, 44138, 53, 8080]:
        r = probe(ip, port)
        p("probe", ip, port, "->", r)
p("=== DONE")
out.close()
'''

# cmdC: gopclntab 解析
CC = r'''
import struct
out = open("/tmp/d158c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
data = open("/tmp/sinit.bin", "rb").read()
p("size", len(data))
cand = 0xa33100
p("magic_at_cand", data[cand:cand+4].hex())
magic = None
for base in [0xa33100, 0x8db000, 0x401000]:
    if data[base:base+4] == b"\xf1\xff\xff\xff":
        magic = base
        break
if magic is None:
    # 全段扫描
    for i in range(0, len(data) - 4, 4):
        if data[i:i+4] == b"\xf1\xff\xff\xff" and data[i+7] == 1:
            magic = i
            p("magic_found_at", hex(i))
            break
if magic is not None:
    nfunc = struct.unpack_from("<I", data, magic + 8)[0]
    textStart = struct.unpack_from("<Q", data, magic + 16)[0]
    fnOff = struct.unpack_from("<I", data, magic + 24)[0]
    p("nfunc", nfunc, "textStart", hex(textStart), "fnOff", fnOff)
    if nfunc < 500000:
        ftab = magic + fnOff
        names = []
        k = ftab
        while k < len(data) and len(names) < nfunc + 50:
            e = data.find(b"\x00", k)
            if e < 0:
                break
            nm = data[k:e]
            k = e + 1
            if len(nm) >= 2:
                names.append(nm)
            if k - ftab > 6000000:
                break
        p("name_count", len(names))
        interesting = []
        for nm in names:
            try:
                t = nm.decode("latin1")
            except Exception:
                continue
            tl = t.lower()
            if any(x in tl for x in ["spawn", "sandbox", "cell", "auth", "sign", "verify", "pubkey",
                                     "ed25519", "command", "exec", "socket", "ping", "kill", "pty",
                                     "connect", "vercel", "mount", "proxy", "policy", "network",
                                     "secret", "token", "credential", "cert", "sinit"]):
                interesting.append(t)
        p("=== FUNCS ===")
        for t in interesting[:900]:
            p("F:", t[:200])
else:
    p("no_magic")
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "extract", timeout=280)
catfile(sid, "/tmp/d158a.txt", "d158a", 2000)

run_cmd(sid, CB, "local-probe", timeout=150)
catfile(sid, "/tmp/d158b.txt", "d158b", 9000)

run_cmd(sid, CC, "gopclntab3", timeout=280)
catfile(sid, "/tmp/d158c.txt", "d158c", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
