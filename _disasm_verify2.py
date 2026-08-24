# -*- coding: utf-8 -*-
"""本地: 读 0x88e016/0x88e021 字符串 + 反汇编 Verifier.verify (0x77ba00)"""
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

d = open("_sandbox_init_new.bin", "rb").read()

# 1) 两个 11 字节字符串
for va, n in [(0x88e016, 20), (0x88e021, 20)]:
    foff = va - 0x400000
    raw = d[foff:foff+n]
    print("STR @%#x: %r" % (va, raw))

# 2) verify 0x77ba00 - 0x77bce0
md = Cs(CS_ARCH_X86, CS_MODE_64)
foff = 0x77ba00 - 0x400000
code = d[foff:foff+0x300]
print("\n" + "="*70 + "\nVerifier.verify @ 0x77ba00\n" + "="*70)
for i in md.disasm(code, 0x77ba00):
    print(f"  {i.address:#x}: {i.mnemonic:8s} {i.op_str}")
