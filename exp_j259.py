# -*- coding: utf-8 -*-
"""实验J259: 直接解析 .gopclntab (off 0x5ab100)
目标: 1) pcHeader 完整字段
     2) functab 定位 + verifierInterceptor 函数 vaddr
     3) dump 目标函数 hex
"""
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

NAME = "expj259"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) gopclntab 头部 dump + 解析
CODE_A = r'''
import shutil, struct
shutil.copy("/run/vercel/share/sandbox-init", "/tmp/si")
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
PC = 0x5ab100  # .gopclntab 文件偏移
hdr = d[PC:PC+64]
p("HDR_HEX", hdr.hex())
magic = struct.unpack("<I", hdr[0:4])[0]
p("magic", hex(magic))
p("pad1", hdr[4], "minLC", hdr[5], "ptrSize", hdr[6])
nfunc = struct.unpack("<I", hdr[7:11])[0]
nfiles = struct.unpack("<I", hdr[11:15])[0]
textStart = struct.unpack("<Q", hdr[15:23])[0]
p("nfunc", nfunc, "nfiles", nfiles, "textStart", hex(textStart))
# 后续 offset 字段 (Go 1.20+: funcname/cu/filetab/pctab/pcln)
off = 23
for name in ("funcnameOffset", "cuOffset", "filetabOffset", "pctabOffset", "pclnOffset"):
    v = struct.unpack("<Q", hdr[off:off+8])[0]
    p(name, hex(v))
    off += 8
# 看是否还有更多字段
p("tail_hex", d[PC+63:PC+96].hex())
'''
run_cmd(sid, CODE_A, "A_PCHDR", timeout=100)

# B) functab 解析: 找 verifierInterceptor 函数
CODE_B = r'''
import struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
PC = 0x5ab100
hdr = d[PC:PC+64]
nfunc = struct.unpack("<I", hdr[7:11])[0]
textStart = struct.unpack("<Q", hdr[15:23])[0]
funcnameOff = struct.unpack("<Q", hdr[23:31])[0]
# functab 紧跟 header (Go 1.20+): 每项 8B {funcoff u32, dataoff u32}
# 但 Go 1.22+ 可能不同, 先尝试 8B 项
ftab = PC + 64  # header 实际大小 43->对齐到 64?
# 尝试: header 大小 48 (6 个 uintptr offset *8 + 15 = 63 -> 对齐 64)
# functab: nfunc+1 项
# 找所有 nameoff 含 verifierInterceptor 的
found = []
for idx in range(nfunc):
    e = ftab + idx * 8
    if e + 8 > len(d):
        break
    funcoff, dataoff = struct.unpack("<II", d[e:e+8])
    if funcoff == 0:
        continue
    # dataoff 指向 _func; _func.nameoff 是 int32 @ +4 (Go 1.20+)
    faddr = PC + dataoff  # 文件偏移 (相对 gopclntab 还是 moduledata?)
    if faddr >= len(d) or faddr + 32 > len(d):
        continue
    entryoff = struct.unpack("<I", d[faddr:faddr+4])[0]
    nameoff = struct.unpack("<i", d[faddr+4:faddr+8])[0]
    if nameoff < 0 or nameoff > 0x300000:
        continue
    naddr = PC + funcnameOff + nameoff
    if naddr >= len(d):
        continue
    end = d.find(b"\x00", naddr)
    nm = d[naddr:end].decode(errors="replace")
    if "verifierInterceptor" in nm or "checkSignature" in nm or ("auth" in nm and "Interceptor" in nm):
        vaddr = textStart + entryoff
        found.append((nm, vaddr))
        p("FUNC", nm, hex(vaddr), "entryoff", hex(entryoff), "nameoff", nameoff)
print("FOUND", len(found), flush=True)
'''
run_cmd(sid, CODE_B, "B_FUNCS", timeout=280)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
