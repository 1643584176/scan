# -*- coding: utf-8 -*-
"""本地: dump 0x5067c0-0x506a00 与 0x509220-0x509700 可读字符串"""
import re

d = open("_sandbox_init_new.bin", "rb").read()

for base in (0x5067c0, 0x509220):
    foff = base - 0x400000
    chunk = d[foff:foff+0x600]
    print("=== %#x ===" % base)
    for m in re.finditer(rb"[ -~]{2,}", chunk):
        print("  %#x: %r" % (base + m.start(), m.group().decode("latin1")))
