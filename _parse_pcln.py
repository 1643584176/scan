# -*- coding: utf-8 -*-
"""本地解析: 新 sandbox-init 的 gopclntab (Go 1.25)
目标: 1) pcHeader 正确布局
     2) functab 解析 -> verifierInterceptor/checkSignature 等函数 vaddr
     3) 输出目标函数表
"""
import struct, sys

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100  # .gopclntab 文件偏移

hdr = d[PC:PC+96]
print("HDR:", hdr[:64].hex())

# 尝试多种布局
def try_layout(name, nfunc_off, nfunc_size, off_off, off_size, n_offsets):
    magic = struct.unpack("<I", hdr[0:4])[0]
    if magic not in (0xfffffff0, 0xfffffff1, 0xfffffff2, 0xfffffff3, 0xfffffffb):
        return None
    nfunc = struct.unpack("<I", hdr[nfunc_off:nfunc_off+nfunc_size])[0] if nfunc_size == 4 else \
            struct.unpack("<Q", hdr[nfunc_off:nfunc_off+nfunc_size])[0]
    if not (1000 < nfunc < 200000):
        return None
    textStart = struct.unpack("<Q", hdr[15:23])[0]
    if not (0x400000 < textStart < 0x2000000):
        return None
    res = {"name": name, "magic": hex(magic), "nfunc": nfunc, "textStart": hex(textStart)}
    o = off_off
    for i in range(n_offsets):
        v = struct.unpack("<I", hdr[o:o+off_size])[0] if off_size == 4 else \
            struct.unpack("<Q", hdr[o:o+off_size])[0]
        res[f"off{i}"] = v
        o += off_size
    return res

for nf_off, nf_sz, of_sz, n_off in ((7, 4, 8, 5), (7, 4, 8, 6), (7, 8, 8, 5), (7, 8, 8, 6), (7, 4, 4, 6), (7, 8, 4, 6)):
    r = try_layout(f"nfunc@{nf_off}+{nf_sz} off@{nf_off+nf_sz}+{of_sz} x{n_off}", nf_off, nf_sz, nf_off+nf_sz, of_sz, n_off)
    if r:
        print("LAYOUT:", r)

# Go 1.18-1.19 紧凑: magic(4) pad1(1) minLC(1) ptrSize(1) nfunc(int,8) nfiles(uint,8) textStart(8) funcname(8) cu(8) filetab(8) pctab(8) pcln(8)
# Go 1.20-1.21 同上但 magic 0xfffffff2
# Go 1.22+ 末尾加 fctab(8)
magic = struct.unpack("<I", hdr[0:4])[0]
pad1, minLC, ptrSize = hdr[4], hdr[5], hdr[6]
nfunc8 = struct.unpack("<Q", hdr[7:15])[0]
nfiles8 = struct.unpack("<Q", hdr[15:23])[0]
textStart = struct.unpack("<Q", hdr[23:31])[0]
print(f"\ncompact: magic={hex(magic)} pad1={pad1} minLC={minLC} ptrSize={ptrSize}")
print(f"  nfunc={nfunc8} nfiles={nfiles8} textStart={hex(textStart)}")
# 若 nfunc 太大 -> 试试 nfunc @7 是 4字节
nfunc4 = struct.unpack("<I", hdr[7:11])[0]
nfiles4 = struct.unpack("<I", hdr[11:15])[0]
textStartA = struct.unpack("<Q", hdr[15:23])[0]
print(f"  alt4: nfunc={nfunc4} nfiles={nfiles4} textStart={hex(textStartA)}")
