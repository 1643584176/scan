# -*- coding: utf-8 -*-
import re
p = r"C:\Users\lbb.LAPTOP-LU4P5L6T\.qoder\cache\projects\scan-dcb95ef8\agent-tools\4164fe49\4a64733f.txt"
txt = open(p, encoding="utf-8", errors="replace").read()
for kw in ("web-access", "web access", "passwordless", "SQL Editor"):
    for m in re.finditer(kw, txt, re.I):
        s = max(0, m.start() - 400)
        seg = txt[s:m.end() + 500].replace("\n", " ")
        print("=== [%s] ...%s" % (kw, seg))
        print()
