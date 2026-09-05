# -*- coding: utf-8 -*-
"""extract large context around searchapi.php def + search its usages in main.js"""
import re

f = "_js/z_main-8efa4cf644fa76389041.js"
s = open(f, "r", encoding="utf-8", errors="replace").read()

i = s.find("searchapi.php")
print("DEF CONTEXT:\n", s[max(0, i - 3000):i + 200], "\n\n====")
# search backward for "An=" assignment
j = s.rfind("An=", max(0, i - 5000), i)
print("An= at", j)
if j >= 0:
    print("An assignment:", s[j:j + 200])
    # all uses of An within file - count & sample
    for mm in list(re.finditer(r"\bAn\b", s))[:40]:
        p = mm.start()
        ctx = s[max(0, p - 120):p + 140].replace("\n", " ")
        print("USE:", ctx[:260])
        print("  ---")
print("done", flush=True)
