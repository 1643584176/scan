# -*- coding: utf-8 -*-
"""实验J258: 新二进制 (hive-containers) gopclntab 正确解析
目标: 1) ELF sections 布局 (找 .gopclntab/.text)
     2) pcHeader: magic/nfunc/textStart/funcnameOffset 确认
     3) functab + funcnametab 解析 -> verifierInterceptor 相关函数 vaddr
     4) dump 目标函数 hex (前 512B) 供本地 capstone 反汇编
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

NAME = "expj258"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) ELF sections 完整布局
CODE_A = r'''
import shutil, struct
shutil.copy("/run/vercel/share/sandbox-init", "/tmp/si")
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
if d[4] == 2:
    # ELF64
    shoff = struct.unpack("<Q", d[0x28:0x30])[0]
    shentsize = struct.unpack("<H", d[0x3a:0x3c])[0]
    shnum = struct.unpack("<H", d[0x3c:0x3e])[0]
    shstrndx = struct.unpack("<H", d[0x3e:0x40])[0]
    p("ELF64", "shoff", hex(shoff), "shentsize", shentsize, "shnum", shnum, "shstrndx", shstrndx)
    # section name table
    shstr_off = struct.unpack("<Q", d[shoff + shstrndx*shentsize + 0x18:shoff + shstrndx*shentsize + 0x20])[0]
    for i in range(shnum):
        e = shoff + i*shentsize
        name_off = struct.unpack("<I", d[e:e+4])[0]
        sh_type = struct.unpack("<I", d[e+4:e+8])[0]
        sh_flags = struct.unpack("<Q", d[e+8:e+16])[0]
        sh_addr = struct.unpack("<Q", d[e+0x10:e+0x18])[0]
        sh_offset = struct.unpack("<Q", d[e+0x18:e+0x20])[0]
        sh_size = struct.unpack("<Q", d[e+0x20:e+0x28])[0]
        name = d[shstr_off+name_off:d.find(b"\x00", shstr_off+name_off)].decode(errors="replace")
        p("SEC", name, "type", sh_type, "addr", hex(sh_addr), "off", hex(sh_offset), "size", hex(sh_size))
'''
run_cmd(sid, CODE_A, "A_SECTIONS", timeout=100)

# B) .gopclntab pcHeader 解析
CODE_B = r'''
import struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
# 已知 buildinfo @ 0x84c000 (A段可确认 gopclntab 实际位置)
# 直接尝试常见 magic 序列
for m in (b"\xfb\xff\xff\xff", b"\xf2\xff\xff\xff", b"\xf3\xff\xff\xff", b"\xf1\xff\xff\xff", b"\xf0\xff\xff\xff", b"\xfa\xff\xff\xff"):
    pos = 0
    cnt = 0
    while True:
        i = d.find(m, pos)
        if i < 0 or cnt >= 8:
            break
        cnt += 1
        # 检查上下文: 后面 1+1+1+4+4+8 字段合理性
        if i+23 <= len(d):
            nfunc = struct.unpack("<I", d[i+7:i+11])[0]
            textStart = struct.unpack("<Q", d[i+15:i+23])[0]
            if nfunc > 1000 and nfunc < 1000000 and textStart > 0x400000 and textStart < 0x1000000:
                p("CAND", m.hex(), hex(i), "nfunc", nfunc, "textStart", hex(textStart))
                # funcnameOffset @ +23
                fo = struct.unpack("<I", d[i+23:i+27])[0]
                p("  funcnameOff", hex(fo))
        pos = i + 1
    p("SCAN", m.hex(), "cnt", cnt)
'''
run_cmd(sid, CODE_B, "B_PCLN", timeout=150)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
