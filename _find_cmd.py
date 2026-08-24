# -*- coding: utf-8 -*-
"""本地: 搜 name=command 及相关 tag"""
import re

d = open("_sandbox_init_new.bin", "rb").read()

for pat in [rb"name=command", rb"name=cmd", rb"name=args", rb"name=argv",
            rb"name=executable", rb"name=entrypoint", rb"name=image"]:
    for m in re.finditer(pat, d):
        s = max(0, m.start()-60)
        ctx = d[s:m.start()+90]
        print("%r @%#x: %r" % (pat, m.start(), ctx.decode("latin1", "replace")))
        print()
