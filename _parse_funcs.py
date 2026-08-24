# -*- coding: utf-8 -*-
"""本地: functab (pcln) 完整解析 -> 目标函数 vaddr
布局: pcHeader(64B) + funcnametab@0x60 + cutab@0x8be20 + filetab@0x924e0
      + pctab@0x9d480 + pcln(functab)@0x1bfc00
functab 项: {entryoff u32, dataoff u32}, dataoff 相对 pclntab 起始 -> _func
_func: {entryOff(4) nameOff(4) args(4) pcsp(4) pcfile(4) pcln(4) ...}
name = funcnametab[nameoff]
"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100
FUNCNAME_OFF = 0x60
FTAB_OFF = 0x1bfc00
TEXT_START = 0x401000
NFUNC = 9870

def read_name(nameoff):
    naddr = PC + FUNCNAME_OFF + nameoff
    if naddr < 0 or naddr >= len(d):
        return None
    end = d.find(b"\x00", naddr)
    if end < 0 or end - naddr > 300:
        return None
    return d[naddr:end].decode(errors="replace")

ftab = PC + FTAB_OFF
funcs = []
for i in range(NFUNC + 1):
    e = ftab + i * 8
    if e + 8 > len(d):
        break
    entryoff, dataoff = struct.unpack("<II", d[e:e+8])
    if dataoff == 0:
        continue
    faddr = PC + dataoff  # 相对 pclntab 起始
    if faddr + 32 > len(d):
        continue
    eoff = struct.unpack("<I", d[faddr:faddr+4])[0]
    nameoff = struct.unpack("<i", d[faddr+4:faddr+8])[0]
    if nameoff < 0:
        continue
    nm = read_name(nameoff)
    if nm:
        funcs.append((nm, TEXT_START + eoff, eoff))

print(f"parsed {len(funcs)} funcs")

# 目标函数
targets = ["verifierInterceptor", "checkSignature", "NewVerifierFromBase64",
           "SpawnInteractive", "SpawnService", "WrapUnary", "wrapUnary",
           "auth", "verify", "Verify"]
for nm, vaddr, eoff in funcs:
    low = nm.lower()
    if any(t.lower() in low for t in targets):
        if "sandbox" in low or "auth" in low or "spawn" in low or "verif" in low or "intercept" in low:
            print(f"FUNC {nm}  vaddr={hex(vaddr)} entryoff={hex(eoff)}")
