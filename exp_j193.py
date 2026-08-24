# 实验J193: A)buildinfo变量名(神秘串身份) B)中间件字符串全览 C)修复symtab D)公钥32字节定位 E)签名工具检查
# j192: 神秘串在buildinfo区0xf88(-X注入); "missing signature header"/"missing timestamp header"自定义中间件
#       symtab解析bug(size==0过滤全函数); 本步修复+全部相关函数列表
import json, time, urllib.request, urllib.error, sys, base64
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

def bashfile(sid, cmd, label, n=20000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj193"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

PUBKEY_B64 = "WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE"

CODE = r'''
import os, struct, base64
out = open("/tmp/d193.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
PATH = "/run/vercel/share/sandbox-init"
f = open(PATH, "rb")
fsize = os.fstat(f.fileno()).st_size

# PA: dump buildinfo 区 (0x600-0x1800) 看 -X 变量名
p("CP", "PA")
f.seek(0x600)
d = f.read(0x1200)
p("BUILDINFO", d.replace(b"\x00", b".").replace(b"\n", b" ")[:2900])
out.flush()

# PB: dump 中间件字符串区 0x5f6000-0x5f9000
p("CP", "PB")
f.seek(0x5f6000)
d = f.read(0x3000)
p("MIDDLEWARE", d.replace(b"\x00", b".").replace(b"\n", b" ")[:3800])
out.flush()

# PC: 修复 symtab (去掉size==0过滤)
p("CP", "PC")
f.seek(0)
eh = f.read(64)
e_shoff = struct.unpack_from("<Q", eh, 40)[0]
e_shentsize = struct.unpack_from("<H", eh, 58)[0]
e_shnum = struct.unpack_from("<H", eh, 60)[0]
e_shstrndx = struct.unpack_from("<H", eh, 62)[0]
f.seek(e_shoff)
shdrs = [f.read(e_shentsize) for _ in range(e_shnum)]
sh = shdrs[e_shstrndx]
shstr_off = struct.unpack_from("<Q", sh, 24)[0]
shstr_sz = struct.unpack_from("<Q", sh, 32)[0]
f.seek(shstr_off)
shstr = f.read(shstr_sz)
def sname(off):
    end = shstr.find(b"\x00", off)
    return shstr[off:end].decode(errors="replace")
sections = {}
for i, sh in enumerate(shdrs):
    nm = sname(struct.unpack_from("<I", sh, 0)[0])
    sections[nm] = (struct.unpack_from("<Q", sh, 24)[0], struct.unpack_from("<Q", sh, 32)[0], i)
st_off, st_sz, _ = sections[".symtab"]
str_off, str_sz, _ = sections[".strtab"]
f.seek(st_off)
symtab = f.read(st_sz)
f.seek(str_off)
strtab = f.read(str_sz)
def sym_name(nmoff):
    end = strtab.find(b"\x00", nmoff)
    return strtab[nmoff:end].decode(errors="replace")
n = st_sz // 24
kw = ("ed25519", "verify", "Verify", "signature", "auth", "Auth", "sign",
      "nonce", "middleware", "Middleware", "interceptor", "Interceptor",
      "Spawn", "spawn", "Ping", "Handler", "connect", "Connect",
      "main.", "bees")
found = []
for i in range(n):
    e = symtab[i * 24:(i + 1) * 24]
    nmoff = struct.unpack_from("<I", e, 0)[0]
    info = e[4]
    shndx = struct.unpack_from("<H", e, 6)[0]
    val = struct.unpack_from("<Q", e, 8)[0]
    size = struct.unpack_from("<Q", e, 16)[0]
    typ = info >> 4
    if typ != 2 or shndx == 0:
        continue
    nm = sym_name(nmoff)
    if any(k in nm for k in kw):
        found.append((val, size, nm))
p("FUNCS_MATCH", len(found))
for val, size, nm in found[:600]:
    p("SYM", hex(val), size, nm[:150])
out.flush()

# PD: base64解码公钥 -> 搜 /proc/1/mem data+heap
p("CP", "PD")
try:
    pk = base64.b64decode("%s==" % "WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE")
except Exception as ex:
    pk = base64.b64decode("WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE")
p("PKLEN", len(pk), pk.hex())
fd = os.open("/proc/1/mem", os.O_RDONLY)
hits = []
# data 0xe30000-0xe9e000 + heap 0xe9e000-0x2ee2000
for (a, b) in [(0xe30000, 0x2ee2000)]:
    pos = a
    while pos < b:
        os.lseek(fd, pos, 0)
        d = os.read(fd, 65536)
        if not d:
            break
        idx = d.find(pk)
        if idx >= 0:
            hits.append(hex(pos + idx))
        pos += len(d)
os.close(fd)
p("PKHITS", hits if hits else "NONE")
out.flush()

# PE: 签名工具检查
p("CP", "PE")
import shutil
p("WHICH_OPENSSL", shutil.which("openssl"))
p("WHICH_CURL", shutil.which("curl"))
try:
    import cryptography
    p("HAS_CRYPTOGRAPHY", cryptography.__version__)
except Exception as ex:
    p("NO_CRYPTOGRAPHY", repr(ex)[:80])
try:
    import nacl
    p("HAS_NACL", nacl.__version__)
except Exception:
    p("NO_NACL")
# 纯python ed25519? 检查
try:
    import ed25519
    p("HAS_PYED25519")
except Exception:
    p("NO_PYED25519")

f.close()
p("done")
out.close()
'''

st = run_cmd(sid, CODE, "J193", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d193.txt", "marker", 22000)
if st == "DEAD":
    print("\n!!! DEATH -> trigger located in marker above", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
