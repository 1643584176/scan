# -*- coding: utf-8 -*-
"""本地: 反汇编 WrapUnary.func1 (0x77b520) 全区域, 找 header 名 + 缺头分支"""
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

d = open("_sandbox_init_new.bin", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)

def disasm(vaddr, size, label):
    foff = vaddr - 0x400000
    code = d[foff:foff+size]
    print(f"\n{'='*70}\n{label} @ {hex(vaddr)}\n{'='*70}")
    for i in md.disasm(code, vaddr):
        print(f"  {i.address:#x}: {i.mnemonic:8s} {i.op_str}")

# WrapUnary.func1 0x77b520 -> 0x77b740 (0x220)
disasm(0x77b520, 0x220, "WrapUnary.func1")

# 顺便看 0x77b740 前几个指令 (WrapStreamingHandler 入口)
disasm(0x77b740, 0x40, "WrapStreamingHandler.entry")
