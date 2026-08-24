# 实验J59: pclntab magic 上下文诊断 + 多 magic 变体 + 备选: patch 字符串引用
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj59"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, struct, subprocess, json, time, ctypes, base64

b = open("/run/vercel/share/sandbox-init", "rb").read()
print("binary size: %d" % len(b), flush=True)

print("===== [0] ELF 头 =====", flush=True)
print("magic:", b[:16].hex(), flush=True)
e_phoff = struct.unpack_from("<Q", b, 0x20)[0]
e_phentsize = struct.unpack_from("<H", b, 0x36)[0]
e_phnum = struct.unpack_from("<H", b, 0x38)[0]
print("phoff=%s phentsize=%d phnum=%d" % (hex(e_phoff), e_phentsize, e_phnum), flush=True)
for i in range(min(e_phnum, 20)):
    o = e_phoff + i * e_phentsize
    p_type, p_flags = struct.unpack_from("<II", b, o)
    p_offset, p_vaddr = struct.unpack_from("<QQ", b, o+8)
    p_filesz, p_memsz = struct.unpack_from("<QQ", b, o+32)
    print("PH %d type=%d flags=%s off=%s vaddr=%s filesz=%s memsz=%s" % (
        i, p_type, hex(p_flags), hex(p_offset), hex(p_vaddr), hex(p_filesz), hex(p_memsz)), flush=True)

print("===== [1] magic 变体扫描 =====", flush=True)
variants = {
    "F1": b"\xf1\xff\xff\xff",
    "F2": b"\xf2\xff\xff\xff",
    "F8": b"\xf8\xff\xff\xff",
    "FB": b"\xfb\xff\xff\xff",
    "FA": b"\xfa\xff\xff\xff",
}
for vn, pat in variants.items():
    idxs = [m.start() for m in re.finditer(re.escape(pat), b)]
    print("%s: %d hits" % (vn, len(idxs)), flush=True)
    for ix in idxs[:8]:
        print("   %s: %s" % (hex(ix), b[ix:ix+32].hex()), flush=True)

print("===== [2] 诊断 FB magic 的解析失败原因 =====", flush=True)
for ix in [m.start() for m in re.finditer(re.escape(b"\xfb\xff\xff\xff"), b)][:10]:
    try:
        pad1 = b[ix+4]; pad2 = b[ix+5]; minLC = b[ix+6]; ptrSize = b[ix+7]
        nfunc = struct.unpack_from("<Q", b, ix+8)[0]
        nfiles = struct.unpack_from("<Q", b, ix+16)[0]
        textStart = struct.unpack_from("<Q", b, ix+24)[0]
        print("%s: pad=%d,%d minLC=%d ptrSize=%d nfunc=%d nfiles=%d textStart=%s" % (
            hex(ix), pad1, pad2, minLC, ptrSize, nfunc, nfiles, hex(textStart)), flush=True)
    except Exception as e:
        print("%s: ERR %s" % (hex(ix), e), flush=True)

print('===== [3] 字符串 invalid-signature 引用 =====', flush=True)
i = b.find(b"invalid signature")
print("invalid signature @ %s" % hex(i), flush=True)
# 找谁引用它 (x86-64: lea rX, [rip+disp32] -> 48 8d xx xx xx xx xx)
target = i
# 文件偏移 -> 虚拟地址 (需要段映射)
# 先假设在 rodata 段 (r--p), 用 ELF 段算
text_va = None
for k in range(min(e_phnum, 20)):
    o = e_phoff + k * e_phentsize
    p_type, p_flags = struct.unpack_from("<II", b, o)
    p_offset = struct.unpack_from("<Q", b, o+8)[0]
    p_vaddr = struct.unpack_from("<Q", b, o+16)[0]
    p_filesz = struct.unpack_from("<Q", b, o+32)[0]
    if p_offset <= i < p_offset + p_filesz:
        text_va = p_vaddr + (i - p_offset)
        print("string va: %s (seg %d)" % (hex(text_va), k), flush=True)
# 反搜引用: 找 RIP 相对 lea 编码
if text_va:
    hits = []
    for m in re.finditer(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d](.{4})", b):
        disp = struct.unpack("<i", m.group(1))[0]
        # 计算目标: 下一条指令地址 (rip)
        # 需要知道 m.start() 的虚拟地址
        for k in range(min(e_phnum, 20)):
            o = e_phoff + k * e_phentsize
            p_offset = struct.unpack_from("<Q", b, o+8)[0]
            p_vaddr = struct.unpack_from("<Q", b, o+16)[0]
            p_filesz = struct.unpack_from("<Q", b, o+32)[0]
            if p_offset <= m.start() < p_offset + p_filesz:
                va = p_vaddr + (m.start() - p_offset)
                target_va = va + len(m.group(0)) + disp
                if target_va == text_va:
                    hits.append(va)
                break
    print("references: %s" % [hex(x) for x in hits[:10]], flush=True)
    for va in hits[:5]:
        print("xref ctx @ %s: %s" % (hex(va), b[va - 32:va + 48].hex()), flush=True)
'''
run_cmd(sid, SCAN, "pclntab-diag", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
