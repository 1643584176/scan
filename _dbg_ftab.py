# -*- coding: utf-8 -*-
"""调试: functab 前 10 项 + dataoff 基准测试"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100
FTAB_OFF = 0x1bfc00
ftab = PC + FTAB_OFF

print("functab first 10 entries:")
for i in range(10):
    e = ftab + i * 8
    entryoff, dataoff = struct.unpack("<II", d[e:e+8])
    print(f"  [{i}] entryoff={entryoff:#x} dataoff={dataoff:#x}")

# 测试 dataoff 不同基准
entryoff, dataoff = struct.unpack("<II", d[ftab:ftab+8])
for name, base in (("PC", PC), ("textStart", 0x401000), ("moduledata0", 0x9ab100 - PC), ("zero", 0)):
    fa = base + dataoff
    if 0 <= fa + 32 <= len(d):
        eoff = struct.unpack("<I", d[fa:fa+4])[0]
        nameoff = struct.unpack("<i", d[fa+4:fa+8])[0]
        print(f"  base={name}: _func@0x{fa:x} eoff={eoff:#x} nameoff={nameoff:#x}")
        # 读 name (试试 funcnametab@0x60)
        naddr = PC + 0x60 + nameoff
        if 0 <= naddr < len(d):
            end = d.find(b"\x00", naddr)
            if end > 0 and end - naddr < 200:
                print(f"    name: {d[naddr:end].decode(errors='replace')}")
