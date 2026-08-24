# -*- coding: utf-8 -*-
"""本地: 输出 sandbox-controller 业务函数 (过滤标准库)"""
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
        funcs.append((nm, TEXT_START + entryoff))

# 业务函数: hive-containers / sandboxinit / spawn 包
out = []
for nm, vaddr in funcs:
    if "hive-containers" in nm or "sandboxinit" in nm or "/spawn" in nm or "spawnv1" in nm:
        out.append((nm, vaddr))
for nm, vaddr in sorted(out, key=lambda x: x[1]):
    print(f"{hex(vaddr)}  {nm}")
print(f"\ntotal business funcs: {len(out)}")
