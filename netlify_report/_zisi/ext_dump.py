# -*- coding: utf-8 -*-
"""Dump 引用点附近反汇编,理解 URL 拼接与 token 使用"""
import sys
sys.path.insert(0, r'D:\scan\netlify_report\_zisi')
from elftools.elf.elffile import ELFFile
import capstone

BIN = r'D:\scan\netlify_report\_ext_binary.bin'
POINTS = [0x4f1f6f, 0x435e32, 0x466d79, 0x47a8b0, 0x4e4fdc, 0x4e50ce, 0x4e50e0]
WIN = 220  # 前后指令窗口(字节)

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

for pt in POINTS:
    start = max(t_addr, pt - WIN)
    end = min(t_addr + t_size, pt + WIN)
    print('=' * 100)
    print('around %#x' % pt)
    for ins in md.disasm(code[start - t_addr:end - t_addr], start):
        mark = ' >>>' if ins.address == pt else '    '
        print('%s %#x: %-8s %s' % (mark, ins.address, ins.mnemonic, ins.op_str))
