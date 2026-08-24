# -*- coding: utf-8 -*-
"""本地: 反汇编新 verify 链 (WrapUnary.func1 / WrapStreamingHandler.func1 / Verifier.verify)
文件偏移 = vaddr - 0x400000
"""
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

d = open("_sandbox_init_new.bin", "rb").read()

def disasm(vaddr, size, label):
    foff = vaddr - 0x400000
    code = d[foff:foff+size]
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    print(f"\n{'='*70}\n{label} @ {hex(vaddr)} ({size}B)\n{'='*70}")
    for i in md.disasm(code, vaddr):
        print(f"  {i.address:#x}: {i.mnemonic:8s} {i.op_str}")

# WrapUnary.func1 @ 0x77b520 (到下一函数 0x77b740, 取 0x230)
disasm(0x77b520, 0x230, "WrapUnary.func1")
# Verifier.verify @ 0x77ba00 (到下一个函数未知, 取 0x400 看开头)
disasm(0x77ba00, 0x300, "Verifier.verify")
