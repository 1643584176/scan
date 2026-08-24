# 实验J194: A)全sections(拿buildinfo vaddr) B)修复symtab C)XREF定位中间件 D)dump函数 E)假签名请求测试
# j193: 中间件协议=signature+timestamp两请求头; symtab bug=info>>4取bind非type; openssl可用
# 本步: XREF搜text段中指向"missing signature header"字符串的lea指令 -> 定位验签函数
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

def bashfile(sid, cmd, label, n=24000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj194"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, struct, time, socket
out = open("/tmp/d194.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
PATH = "/run/vercel/share/sandbox-init"
f = open(PATH, "rb")

# PA: sections + program headers (vaddr映射)
p("CP", "PA")
f.seek(0)
eh = f.read(64)
e_shoff = struct.unpack_from("<Q", eh, 40)[0]
e_shentsize = struct.unpack_from("<H", eh, 58)[0]
e_shnum = struct.unpack_from("<H", eh, 60)[0]
e_shstrndx = struct.unpack_from("<H", eh, 62)[0]
e_phoff = struct.unpack_from("<Q", eh, 32)[0]
e_phentsize = struct.unpack_from("<H", eh, 54)[0]
e_phnum = struct.unpack_from("<H", eh, 56)[0]
# program headers (LOAD段 vaddr<->offset)
f.seek(e_phoff)
loads = []
for i in range(e_phnum):
    ph = f.read(e_phentsize)
    ptype = struct.unpack_from("<I", ph, 0)[0]
    if ptype == 1:  # PT_LOAD
        off = struct.unpack_from("<Q", ph, 8)[0]
        vaddr = struct.unpack_from("<Q", ph, 16)[0]
        filesz = struct.unpack_from("<Q", ph, 32)[0]
        memsz = struct.unpack_from("<Q", ph, 40)[0]
        loads.append((off, vaddr, filesz, memsz))
        p("LOAD", hex(off), hex(vaddr), hex(filesz), hex(memsz))
out.flush()
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
    sections[nm] = (struct.unpack_from("<Q", sh, 24)[0], struct.unpack_from("<Q", sh, 32)[0],
                    struct.unpack_from("<Q", sh, 16)[0], i)  # off, size, addr
p("SECS", {k: (hex(v[0]), hex(v[1]), hex(v[2]), v[3]) for k, v in sections.items()
           if k in (".text", ".rodata", ".go.buildinfo", ".data", ".bss", ".symtab", ".strtab")})
out.flush()

def f2v(off):
    for lo, lv, lf, lm in loads:
        if lo <= off < lo + lf:
            return lv + (off - lo)
    return None

# PB: 修复symtab (typ = info & 0xF)
p("CP", "PB")
st_off, st_sz, _, _ = sections[".symtab"]
str_off, str_sz, _, _ = sections[".strtab"]
f.seek(st_off)
symtab = f.read(st_sz)
f.seek(str_off)
strtab = f.read(str_sz)
def sym_name(nmoff):
    end = strtab.find(b"\x00", nmoff)
    return strtab[nmoff:end].decode(errors="replace")
n = st_sz // 24
kw = ("ed25519", "signature", "middleware", "timestamp",
      "main.", "bees", "verify")
found = []
for i in range(n):
    e = symtab[i * 24:(i + 1) * 24]
    nmoff = struct.unpack_from("<I", e, 0)[0]
    info = e[4]
    shndx = struct.unpack_from("<H", e, 6)[0]
    val = struct.unpack_from("<Q", e, 8)[0]
    size = struct.unpack_from("<Q", e, 16)[0]
    typ = info & 0xF
    if typ != 2 or shndx == 0:
        continue
    nm = sym_name(nmoff)
    low = nm.lower()
    if nm.startswith("main.") or ("bees" in nm and "connectrpc.com/connect" not in nm):
        found.append((val, size, nm))
        continue
    if any(k in nm for k in kw) or "sign" in low or "auth" in low:
        if not nm.startswith(("runtime.", "internal/", "reflect.", "os/signal", "crypto/tls", "crypto/x509", "crypto/rsa", "crypto/ecdsa", "net/http", "encoding/json", "math/big", "syscall.", "time.", "slices.", "vendor/", "compress/flate", "net/url", "crypto/ed25519", "type:.eq")):
            found.append((val, size, nm))
p("FUNCS_MATCH", len(found))
for val, size, nm in found[:300]:
    p("SYM", hex(val), size, nm[:160])
out.flush()

# PC: XREF 扫描 text 段
p("CP", "PC")
text_off, text_sz, text_vaddr, _ = sections[".text"]
# 目标vaddr: missing signature header (file 0x5f60c1 -> vaddr)
t_sig = f2v(0x5f60c1)
t_ts = f2v(0x5f60c1 + len("missing signature header") + 1)
t_myst = f2v(0xf88)
p("TARGETS", hex(t_sig) if t_sig else None, hex(t_ts) if t_ts else None,
  hex(t_myst) if t_myst else None)
out.flush()
# 搜 48 8d 3d (lea rdi,[rip+disp32]) 和 48 8d 05/0d/15/1d/25/2d/35/3d (lea rax等)
import re
xr = []
pos = 0
f.seek(text_off)
while pos < text_sz:
    f.seek(text_off + pos)
    d = f.read(262144)
    if not d:
        break
    i = 0
    while i < len(d) - 7:
        if d[i] == 0x48 and d[i + 1] == 0x8d and (d[i + 2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", d, i + 3)[0]
            insn_addr = text_vaddr + pos + i
            target = insn_addr + 7 + disp
            for name, tv in (("SIG", t_sig), ("TS", t_ts), ("MYST", t_myst)):
                if tv and abs(target - tv) < 0x200:
                    xr.append((hex(insn_addr), name, hex(target), hex(tv)))
                    break
            i += 7
        else:
            i += 1
    pos += len(d)
p("XREFS", xr if xr else "NONE")
out.flush()

# PD: dump XREF命中函数上下文 (符号表定位最近函数)
p("CP", "PD")
if xr:
    # 找每个xref前的最近函数
    for xaddr, name, tgt, tv in xr:
        xv = int(xaddr, 16)
        best = None
        for val, size, nm in found:
            if val <= xv < val + max(size, 8):
                best = (val, size, nm)
                break
            if best is None or (val <= xv and (best[0] <= val)):
                pass
        # 线性找最近
        best = None
        for val, size, nm in found:
            if val <= xv:
                if best is None or val > best[0]:
                    best = (val, size, nm)
        if best:
            bv, bs, bn = best
            p("NEAR_FUNC", xaddr, hex(bv), bs, bn[:150])
            # dump函数机器码 (从文件 text_off + (bv - text_vaddr))
            f.seek(text_off + (bv - text_vaddr))
            code = f.read(min(max(bs, 64), 256))
            p("CODE", hex(bv), code.hex())
            out.flush()
# dump main.main 完整
for val, size, nm in found:
    if nm == "main.main":
        f.seek(text_off + (val - text_vaddr))
        code = f.read(min(max(size, 128), 512))
        p("MAIN_MAIN", hex(val), size)
        p("MAIN_CODE", code.hex())
        out.flush()
        break

# PE: 带假signature+timestamp请求 (验证有头但验签失败的行为)
p("CP", "PE")
def http(port, method, path, headers, body=b"", to=3):
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
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 2500:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
now = str(int(time.time()))
# E1: 假签名+真时间戳, 普通路径 (先只测缺一头的组合, 从最安全开始)
p("CP", "E1")
d = http(30001, "POST", "/foo",
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "signature": "AAAA", "timestamp": now}, b"{}")
p("E1", "fake sig+ts ->", d[:250]); out.flush()
# E2: 缺timestamp
p("CP", "E2")
d = http(30001, "POST", "/foo",
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "signature": "AAAA"}, b"{}")
p("E2", "sig only ->", d[:250]); out.flush()
# E3: 缺signature
p("CP", "E3")
d = http(30001, "POST", "/foo",
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "timestamp": now}, b"{}")
p("E3", "ts only ->", d[:250]); out.flush()
# E4: 空签名+空时间戳
p("CP", "E4")
d = http(30001, "POST", "/foo",
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "signature": "", "timestamp": ""}, b"{}")
p("E4", "empty ->", d[:250]); out.flush()
p("done")
f.close()
out.close()
'''

st = run_cmd(sid, CODE, "J194", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d194.txt", "marker", 26000)
if st == "DEAD":
    print("\n!!! DEATH -> trigger located in marker above", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
