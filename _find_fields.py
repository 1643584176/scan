# -*- coding: utf-8 -*-
"""本地: 找 SpawnRequest 字段名 (从 proto descriptor 或 strings)"""
import re

d = open("_sandbox_init_new.bin", "rb").read()

# 1) 常见字段名候选
for pat in [rb"command", rb"argv", rb"workingDirector", rb"cwd", rb"env\b", rb"timeout",
            rb"pty", rb"shell", rb"processId", rb"snapshot", rb"snapshotId"]:
    ms = list(re.finditer(pat, d))
    if ms:
        print("PAT %-20s %d hits: %s" % (pat.decode(), len(ms),
              ", ".join(hex(m.start()) for m in ms[:6])))

# 2) 反汇编 SpawnRequest.String (0x773540) 看字段名引用
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
md = Cs(CS_ARCH_X86, CS_MODE_64)
foff = 0x773540 - 0x400000
code = d[foff:foff+0xe0]
print("\nSpawnRequest.String @0x773540")
for i in md.disasm(code, 0x773540):
    print(f"  {i.address:#x}: {i.mnemonic:8s} {i.op_str}")
