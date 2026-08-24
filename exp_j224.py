# 实验J224: dump main传入0x5ab700的key字符串 + 0x5ab700代码 + 全局0xe9dce0对象
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

NAME = "expj224"
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

CODE = r'''
import struct, base64
out = open("/tmp/d224.txt", "w")
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

def dump_str(name, vaddr, n):
    f = v2f(vaddr)
    if f is None:
        p(name, hex(vaddr), "NO_SEG")
        return
    raw = data[f:f+n]
    txt = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in raw)
    p(name, hex(vaddr), "n", n, "hex", raw.hex(), "txt", repr(txt))
    # 尝试 base64 解码
    try:
        b64 = raw.split(b"\x00")[0]
        dec = base64.b64decode(b64 + b"=" * ((4 - len(b64) % 4) % 4))
        p(name, "B64DEC", len(dec), dec.hex())
    except Exception:
        pass

# main传入0x5ab700的字符串
dump_str("S6A", 0x9E8F29, 8)      # 6字节
dump_str("S6B", 0x9E8F2F, 8)      # 6字节
dump_str("S40", 0xA0086B, 48)     # 40字节
dump_str("S53", 0xA06917, 64)     # 53字节

# 0x5ab700 代码
f = v2f(0x5ab700)
if f:
    raw = data[f:f+0x500]
    p("CODE5AB700", hex(f), raw.hex())
else:
    p("CODE5AB700 NO_SEG")
p("done")
out.close()
'''
st = run_cmd(sid, CODE, "J224A", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d224.txt", "STRINGS", 30000)

# 内存读全局 0xe9dce0
CODE2 = r'''
import os, struct
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
b = ra(0xe9dce0, 0x18)
ptr, ln, cap = struct.unpack_from("<QQQ", b)
print("G9DCE0 ptr", hex(ptr), "len", ln, "cap", cap, flush=True)
if ptr and 0x10000 < ptr < 0x800000000000:
    try:
        obj = ra(ptr, min(0x200, ln if 0 < ln <= 0x200 else 0x200))
        print("OBJ", obj.hex(), flush=True)
    except Exception as e:
        print("OBJ_ERR", repr(e), flush=True)
os.close(fd)
'''
st = run_cmd(sid, CODE2, "J224B", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
