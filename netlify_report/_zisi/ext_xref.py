# -*- coding: utf-8 -*-
"""反汇编:找 'lambda-events.services.netlify.com' 字符串引用位置(rip-relative lea)"""
import sys
sys.path.insert(0, r'D:\scan\netlify_report\_zisi')
from elftools.elf.elffile import ELFFile
import capstone

BIN = r'D:\scan\netlify_report\_ext_binary.bin'
TARGETS = [b'https://lambda-events.services.netlify.com', b'https://lambda-events-staging.services.netlify.com',
           b'NETLIFY_FUNCTIONS_TOKEN']

with open(BIN, 'rb') as f:
    elf = ELFFile(f)
    # 找 .text / .rodata 虚拟地址与文件偏移
    text_seg = None
    rodata_seg = None
    for sec in elf.iter_sections():
        if sec.name == '.text':
            text_seg = (sec['sh_addr'], sec['sh_offset'], sec['sh_size'])
        if sec.name == '.rodata':
            rodata_seg = (sec['sh_addr'], sec['sh_offset'], sec['sh_size'])
    print('.text:', text_seg)
    print('.rodata:', rodata_seg)
    f.seek(0)
    data = f.read()

    # 字符串虚拟地址
    def vaddr_of(hay):
        off = data.find(hay)
        if off < 0:
            return None
        for sec in elf.iter_sections():
            sh_off = sec['sh_offset']
            sh_size = sec['sh_size']
            if sh_off <= off < sh_off + sh_size:
                return sec['sh_addr'] + (off - sh_off), off
        return None, off

    str_addrs = {}
    for t in TARGETS:
        va, fo = vaddr_of(t)
        str_addrs[t] = va
        print('target %r -> vaddr %#x (file %#x)' % (t, va, fo))

if not text_seg:
    sys.exit(1)
t_addr, t_off, t_size = text_seg

# 反汇编 .text 找 rip-relative 引用
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
with open(BIN, 'rb') as f:
    f.seek(t_off)
    code = f.read(t_size)

print('disassembling %d bytes...' % len(code))
hits = []
addr_to_name = {va: name for name, va in str_addrs.items() if va}
for ins in md.disasm(code, t_addr):
    if ins.mnemonic in ('lea', 'mov') and ins.operands:
        # 找含内存操作数 [rip+disp]
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                target = ins.address + ins.size + op.mem.disp
                for va, name in addr_to_name.items():
                    if va <= target < va + 200:
                        hits.append((ins.address, name, target - va, ins.mnemonic, ins.op_str))
                        break
print('hits:', len(hits))
for h in hits[:60]:
    print('  %#x: %s %s  (str %r +%d)' % (h[0], h[3], h[4], h[1], h[2]))
