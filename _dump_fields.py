# -*- coding: utf-8 -*-
"""本地: dump 0x5091f0-0x509740 区域的可读字符串 (SpawnRequest 字段名)"""
import re

d = open("_sandbox_init_new.bin", "rb").read()

for base in (0x5091f0, 0x509400, 0x509600):
    foff = base - 0x400000
    chunk = d[foff:foff+0x200]
    print("=== %#x ===" % base)
    for m in re.finditer(rb"[ -~]{3,}", chunk):
        print("  %#x: %r" % (base + m.start(), m.group().decode("latin1")))
