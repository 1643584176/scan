# -*- coding: utf-8 -*-
"""本地: Go 1.25 pcHeader 精确解析 (Go 1.20+ 格式)
pcHeader: magic(4) pad1(1) pad2(1) minLC(1) ptrSize(1) nfunc(8) nfiles(8)
          textStart(8) funcnameOffset(8) cuOffset(8) filetabOffset(8)
          pctabOffset(8) pclnOffset(8) fctabOffset(8)
"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100

hdr = d[PC:PC+96]
magic = struct.unpack("<I", hdr[0:4])[0]
pad1, pad2, minLC, ptrSize = hdr[4], hdr[5], hdr[6], hdr[7]
nfunc = struct.unpack("<Q", hdr[8:16])[0]
nfiles = struct.unpack("<Q", hdr[16:24])[0]
textStart = struct.unpack("<Q", hdr[24:32])[0]
funcnameOffset = struct.unpack("<Q", hdr[32:40])[0]
cuOffset = struct.unpack("<Q", hdr[40:48])[0]
filetabOffset = struct.unpack("<Q", hdr[48:56])[0]
pctabOffset = struct.unpack("<Q", hdr[56:64])[0]
pclnOffset = struct.unpack("<Q", hdr[64:72])[0]
fctabOffset = struct.unpack("<Q", hdr[72:80])[0]

print(f"magic={hex(magic)} pad1={pad1} pad2={pad2} minLC={minLC} ptrSize={ptrSize}")
print(f"nfunc={nfunc} nfiles={nfiles} textStart={hex(textStart)}")
print(f"funcnameOffset={hex(funcnameOffset)} cuOffset={hex(cuOffset)}")
print(f"filetabOffset={hex(filetabOffset)} pctabOffset={hex(pctabOffset)}")
print(f"pclnOffset={hex(pclnOffset)} fctabOffset={hex(fctabOffset)}")

# functab 位置 (Go 1.22+: fctabOffset 相对 pclntab 起始)
ftab_file = PC + fctabOffset
print(f"\nfunctab file offset: {hex(ftab_file)}")
# functab: nfunc+1 项, 每项 {funcoff u32, dataoff u32} (Go 1.20+) 或 {funcoff u32, dataoff u32} x2?
# Go 1.22: 每项 8B. Go 1.23+ 可能 {funcoff, dataoff, funcoff2, dataoff2} 16B?
first = d[ftab_file:ftab_file+32]
print("functab first 32B:", first.hex())

# 尝试 8B 项
e0 = struct.unpack("<II", first[0:8])
e1 = struct.unpack("<II", first[8:16])
print("entry0:", [hex(x) for x in e0], "entry1:", [hex(x) for x in e1])

# 校验: entry0 funcoff 应为 0 (第一个函数), dataoff 指向 _func
# _func 结构 Go 1.22+: entryOff(4) nameOff(4) args(4) pcsp(4) pcfile(4) pcln(4) nfuncdata(1) ncu(1) endc(1) ...
