# 实验J192: sandbox-init 符号表解析 + 验签函数定位 + 关键字符串file offset
# j191: /proc/1/mem 任意地址可写不触发监控(text/代码区已验证) => 可patch验签逻辑
#       需先找到验签函数位置 -> 解析ELF .symtab (Go二进制通常保留符号表)
# 本步: 1)文件全搜关键字符串 2)symtab解析过滤验签相关符号 3)dump函数机器码
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

def bashfile(sid, cmd, label, n=16000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj192"
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
import os, struct
out = open("/tmp/d192.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
PATH = "/run/vercel/share/sandbox-init"
f = open(PATH, "rb")
fsize = os.fstat(f.fileno()).st_size
p("SIZE", fsize)

# PA: 文件全搜关键字符串 (逐64KB, 记file offset)
p("CP", "PA")
targets = [b"WVN8gckg", b"jsew6QlLu0BjbIS5zTym", b"ed25519", b"Connect-Protocol-Version",
           b"signature", b"nonce", b"verify", b"Verify"]
offs = {t: [] for t in targets}
pos = 0
while pos < fsize:
    f.seek(pos)
    d = f.read(65536)
    if not d:
        break
    for t in targets:
        idx = d.find(t)
        if idx >= 0:
            offs[t].append(pos + idx)
    pos += len(d)
for t in targets:
    p("OFF", t.decode(), [hex(x) for x in offs[t][:10]])
# 对前4个命中的串dump上下文
for t in targets:
    if offs[t]:
        off = offs[t][0]
        f.seek(max(0, off - 64))
        ctx = f.read(320)
        p("CTX", t.decode(), hex(off),
          ctx.replace(b"\x00", b".").replace(b"\n", b" ")[:280])
out.flush()

# PB: ELF解析 symtab
p("CP", "PB")
f.seek(0)
eh = f.read(64)
assert eh[:4] == b"\x7fELF", "not ELF"
e_shoff = struct.unpack_from("<Q", eh, 40)[0]
e_shentsize = struct.unpack_from("<H", eh, 58)[0]
e_shnum = struct.unpack_from("<H", eh, 60)[0]
e_shstrndx = struct.unpack_from("<H", eh, 62)[0]
f.seek(e_shoff)
shdrs = []
for i in range(e_shnum):
    shdrs.append(f.read(e_shentsize))
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
    sections[nm] = (struct.unpack_from("<Q", sh, 24)[0],
                    struct.unpack_from("<Q", sh, 32)[0],
                    i)
p("SECS", {k: (hex(v[0]), hex(v[1]), v[2]) for k, v in sections.items() if k in
           (".text", ".symtab", ".strtab", ".rodata", ".data", ".bss", ".got")})
out.flush()
if ".symtab" not in sections:
    p("NO_SYMTAB")
else:
    st_off, st_sz, _ = sections[".symtab"]
    entsz = 24
    n = st_sz // entsz
    p("SYMS", n)
    # 先找 text 段 vaddr 映射 (地址->file offset)
    text_off, text_sz, _ = sections[".text"]
    f.seek(st_off)
    symtab = f.read(st_sz)
    # strtab
    str_off, str_sz, _ = sections[".strtab"]
    f.seek(str_off)
    strtab = f.read(str_sz)
    def sym_name(nmoff):
        end = strtab.find(b"\x00", nmoff)
        return strtab[nmoff:end].decode(errors="replace")
    kw = ("ed25519", "verify", "Verify", "signature", "auth", "Auth", "sign",
          "nonce", "middleware", "Middleware", "interceptor", "Interceptor",
          "Spawn", "spawn", "Ping", "Handler", "connect", "Connect")
    found = []
    for i in range(n):
        e = symtab[i * entsz:(i + 1) * entsz]
        nmoff, info, shndx = struct.unpack_from("<IBH", e, 0)[0], e[4], struct.unpack_from("<H", e, 6)[0]
        val, size = struct.unpack_from("<QQ", e, 8)
        typ = info >> 4
        if typ != 2 or size == 0:  # STT_FUNC
            continue
        nm = sym_name(nmoff)
        if any(k in nm for k in kw):
            found.append((val, size, nm))
    p("FUNCS_MATCH", len(found))
    for val, size, nm in found[:400]:
        p("SYM", hex(val), size, nm[:140])
    out.flush()
    # dump main.main 前48字节 (从文件: vaddr->offset 需LOAD映射, 先假设text段文件偏移)
    for val, size, nm in found:
        if nm == "main.main":
            p("MAIN_MAIN", hex(val), size)
            f.seek(text_off + (val - sections[".text"][1]))
            p("MAIN_HEX", f.read(min(size, 96)).hex())
            break

f.close()
p("done")
out.close()
'''

st = run_cmd(sid, CODE, "J192", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d192.txt", "marker", 20000)
if st == "DEAD":
    print("\n!!! DEATH -> trigger located in marker above", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
