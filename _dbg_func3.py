# -*- coding: utf-8 -*-
"""调试: _func 数据区位置验证
functab @ PC+0x1bfc00, 大小 0x13478 -> _func 区 @ PC+0x1d3078 = 0x788178
"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100

cands = [0x788178, 0x5be578, 0x13478, 0x1d3078, 0x5ab100+0x1d3078]
for F in cands:
    if F + 64 > len(d):
        print(f"@{F:#x}: out of range")
        continue
    raw = d[F:F+48]
    print(f"\n@{F:#x}: {raw.hex()}")
    eoff = struct.unpack("<I", raw[0:4])[0]
    nameoff = struct.unpack("<i", raw[4:8])[0]
    args = struct.unpack("<i", raw[8:12])[0]
    print(f"  eoff={eoff:#x} nameoff={nameoff:#x} args={args:#x}")
    # 尝试多种 name 基准
    for nb, nbname in ((PC+0x60, "funcnametab"), (0x60, "funcnametab_rel"), (PC, "pclntab")):
        naddr = nb + nameoff
        if 0 <= naddr < len(d):
            end = d.find(b"\x00", naddr)
            if end > 0 and end - naddr < 200:
                print(f"  name[{nbname}]: {d[naddr:end].decode(errors='replace')}")
