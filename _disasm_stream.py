# -*- coding: utf-8 -*-
"""本地: WrapStreamingHandler.func1 反汇编 (SpawnInteractive 验证路径) + 确认 call 字节"""
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

d = open("_sandbox_init_new.bin", "rb").read()

# 1) 确认 0x77bb83 处 call 字节
foff = 0x77bb83 - 0x400000
print("verify call bytes @0x77bb83:", d[foff:foff+8].hex())

# 2) WrapStreamingHandler.func1 @ 0x77b7e0 完整 (到 0x77ba00 前, 0x220)
def disasm(vaddr, size, label):
    foff = vaddr - 0x400000
    code = d[foff:foff+size]
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    print(f"\n{'='*70}\n{label} @ {hex(vaddr)}\n{'='*70}")
    for i in md.disasm(code, vaddr):
        print(f"  {i.address:#x}: {i.mnemonic:8s} {i.op_str}")

disasm(0x77b7e0, 0x220, "WrapStreamingHandler.func1")
