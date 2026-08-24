# -*- coding: utf-8 -*-
"""本地: 字符串 xref 定位 verify 拦截器
- rodata 字符串 "missing signature header" @0x4f4a31 -> vaddr = 0x808000 + (0x4f4a31-0x408000) = 0x816a31
- .text 搜 leaq rel32 指向该 vaddr 的指令
"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()

RODATA_VADDR = 0x808000
RODATA_OFF = 0x408000
TEXT_OFF = 0x1000
TEXT_VADDR = 0x401000
TEXT_SIZE = 0x406ed1

def file_to_vaddr(foff):
    if RODATA_OFF <= foff < RODATA_OFF + 0x19f2d9:
        return RODATA_VADDR + (foff - RODATA_OFF)
    if TEXT_OFF <= foff < TEXT_OFF + TEXT_SIZE:
        return TEXT_VADDR + (foff - TEXT_OFF)
    return None

targets = [
    (0x4f4a31, "missing signature header"),
    (0x4f4a45, "missing timestamp header"),
    (0x4f0ad4, "invalid signature"),
]
for toff, tname in targets:
    tv = file_to_vaddr(toff)
    print(f"{tname}: file 0x{toff:x} vaddr 0x{tv:x}" if tv else f"{tname}: NO VADDR")

# 在 .text 中搜索 lea rdi/rax + rel32 指向目标
text = d[TEXT_OFF:TEXT_OFF+TEXT_SIZE]
print(f"\ntext size {len(text)}")
hits = []
for toff, tname in targets:
    tv = file_to_vaddr(toff)
    if not tv:
        continue
    # 常见: 48 8d 3d rel32 (lea rdi), 48 8d 05 rel32 (lea rax), 4c 8d 35 rel32 (lea r14)
    for reg in (b"\x3d", b"\x05", b"\x35", b"\x15", b"\x0d"):
        pat = b"\x48\x8d" + reg
        pos = 0
        cnt = 0
        while True:
            i = text.find(pat, pos)
            if i < 0 or cnt >= 20:
                break
            rel = struct.unpack("<i", text[i+3:i+7])[0]
            insn_vaddr = TEXT_VADDR + i
            target = insn_vaddr + 7 + rel
            if abs(target - tv) < 0x4000:  # 允许一定范围 (字符串引用可能指向中间)
                hits.append((tname, insn_vaddr, target, rel, reg.hex()))
                cnt += 1
            pos = i + 1
for h in hits:
    print(f"XREF {h[0]}: insn 0x{h[1]:x} -> 0x{h[2]:x} (rel {h[3]}) reg {h[4]}")
print(f"total xref hits: {len(hits)}")
