# 实验J215: 1) dump 0xe9f060/0xe9f140指向的heap数据(可能=pub)
# 2) 修复OOM: 用data.find逐关键字搜二进制
# 3) 对照: 全新沙箱直接发请求(不读内存) vs 读内存后发请求
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

def bashfile(sid, cmd, label, n=30000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj215"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 0) 对照实验A: 全新沙箱, 未读内存, 直接发请求 -> 看进程死活 + 响应
CODE_A = r'''
import socket, time
out = open("/tmp/reqa.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

def http(port, method, path, headers, body=b"", to=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        hdrs = f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n"
        for k, v in headers.items():
            hdrs += f"{k}: {v}\r\n"
        hdrs += f"Content-Length: {len(body)}\r\n\r\n"
        s.send(hdrs.encode() + body)
        d = b""
        try:
            while True:
                b2 = s.recv(4096)
                if not b2:
                    break
                d += b2
                if len(d) > 3000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()

p("start")
now = str(int(time.time()))
d1 = http(30001, "POST", "/foo",
          {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
           "X-Timestamp": now}, b"{}")
p("NO_SIG:", d1[:250])
d2 = http(30001, "POST", "/foo",
          {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
           "X-Signature": "AAAA", "X-Timestamp": now}, b"{}")
p("BAD_SIG:", d2[:250])
p("done")
out.close()
'''
st = run_cmd(sid, CODE_A, "REQ_A_FRESH", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/reqa.txt 2>&1", "REQ_A_CAT", 4000)
# 沙箱是否还活着
bashfile(sid, "echo ALIVE; ls /tmp/", "ALIVE_CHECK", 2000)

# 1) dump 0xe9f060/0xe9f140 指向的数据
CODE_B = r'''
import os, struct
out = open("/tmp/dumpb.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
for hdr in (0xe9f060, 0xe9f140):
    try:
        h = ra(hdr, 24)
        ptr, ln, cap = struct.unpack("<QQQ", h)
        p("HDR", hex(hdr), hex(ptr), ln, cap)
        if ptr:
            d = ra(ptr, min(ln, 0x40))
            p("DATA", d.hex())
            ctx = ra(ptr - 0x40, 0x40 + min(ln, 0x40) + 0x80)
            p("CTX", ctx.hex())
    except Exception as e:
        p("ERR", hex(hdr), repr(e))
p("done")
out.close()
os.close(fd)
'''
st = run_cmd(sid, CODE_B, "DUMP_F9", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/dumpb.txt 2>&1", "DUMP_F9_CAT", 5000)

# 2) 二进制关键字搜索(修复OOM: data.find + 上下文)
CODE_C = r'''
import re
out = open("/tmp/strc.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)
data = open("/tmp/si", "rb").read()
kws = [b"verify", b"Verify", b"ed25519", b"Ed25519", b"signature", b"Signature",
       b"pubkey", b"PublicKey", b"X-Signature", b"x-signature", b"jws", b"jwt",
       b"invalid", b"token", b"Timestamp", b"timestamp"]
for kw in kws:
    cnt = 0
    pos = 0
    while True:
        i = data.find(kw, pos)
        if i < 0:
            break
        if cnt < 3:
            ctx = data[max(0, i - 30):i + len(kw) + 40]
            p("KW", kw.decode(), hex(i), ctx.decode("utf-8", "replace").replace("\n", "\\n")[:120])
        cnt += 1
        pos = i + 1
    p("CNT", kw.decode(), cnt)
p("done")
out.close()
'''
st = run_cmd(sid, CODE_C, "BIN_KW", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/strc.txt 2>&1 | head -80", "BIN_KW_CAT", 12000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
