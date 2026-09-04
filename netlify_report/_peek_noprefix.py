# -*- coding: utf-8 -*-
# _peek_noprefix.py - find base url handling with noPrefix flag
import os, re
src = open(r"D:\scan\netlify_report\_js\net_lib.js", encoding="utf-8", errors="replace").read()
# find request function definition
i = src.find("noPrefix")
while i >= 0:
    seg = src[max(0, i-600):i+600]
    if "request" in seg or "base" in seg.lower() or "url" in seg.lower():
        print("### @", i)
        print(seg)
        print("----")
    j = src.find("noPrefix", i + 8)
    if j == i:
        break
    i = j
