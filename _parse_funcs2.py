# -*- coding: utf-8 -*-
"""本地: functab 完整解析 (修正版)
- functab @ PC+0x1bfc00, 每项 {entryoff u32, dataoff u32}
- dataoff 相对 functab 区起始 -> _func 文件偏移 = PC + 0x1bfc00 + dataoff
- _func: {entryOff(4) nameOff(4) args(4) ...}
- name = funcnametab[PC+0x60 + nameoff]
- vaddr = textStart + entryoff (textStart=0x401000)
"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100
FTAB_REL = 0x1bfc00
FUNCNAME_REL = 0x60
TEXT_START = 0x401000
NFUNC = 9870

def read_name(nameoff):
    naddr = PC + FUNCNAME_REL + nameoff
    if naddr < 0 or naddr >= len(d):
        return None
    end = d.find(b"\x00", naddr)
    if end < 0 or end - naddr > 400:
        return None
    return d[naddr:end].decode(errors="replace")

ftab = PC + FTAB_REL
funcs = []
for i in range(NFUNC + 1):
    e = ftab + i * 8
    if e + 8 > len(d):
        break
    entryoff, dataoff = struct.unpack("<II", d[e:e+8])
    if dataoff == 0:
        continue
    faddr = PC + FTAB_REL + dataoff
    if faddr + 32 > len(d):
        continue
    nameoff = struct.unpack("<i", d[faddr+4:faddr+8])[0]
    if nameoff < 0:
        continue
    nm = read_name(nameoff)
    if nm:
        funcs.append((nm, TEXT_START + entryoff, entryoff))

print(f"parsed {len(funcs)} funcs")

# 输出 auth/spawn/verify 相关函数
kws = ["sandboxinit", "spawn", "auth", "verif", "intercept", "signature",
       "SpawnService", "checkSign", "service"]
seen = set()
for nm, vaddr, eoff in funcs:
    low = nm.lower()
    if any(k in low for k in kws):
        key = nm
        if key in seen:
            continue
        seen.add(key)
        print(f"FUNC {nm}  vaddr={hex(vaddr)}")
