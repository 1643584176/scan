# -*- coding: utf-8 -*-
"""Dump token 引用簇 0x4e4e00-0x4e5200 与 URL 0x4f1e00-0x4f2100 全量"""
import sys
sys.path.insert(0, r'D:\scan\netlify_report\_zisi')
from elftools.elf.elffile import ELFFile
import capstone

BIN = r'D:\scan\netlify_report\_ext_binary.bin'
RANGES = [(0x4e4d80, 0x4e5280), (0x4f1e00, 0x4f2100)]

with open(BIN, 'rb') as f:
    elf = ELFFile(f)
    for sec in elf.iter_sections():
        if sec.name == '.text':
            t_addr, t_off, t_size = sec['sh_addr'], sec['sh_offset'], sec['sh_size']

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
with open(BIN, 'rb') as f:
    f.seek(t_off)
    code = f.read(t_size)

for (s0, s1) in RANGES:
    print('=' * 110)
    print('range %#x - %#x' % (s0, s1))
    for ins in md.disasm(code[s0 - t_addr:s1 - t_addr], s0):
        print('  %#x: %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
