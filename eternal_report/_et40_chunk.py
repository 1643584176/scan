# -*- coding: utf-8 -*-
"""find searchapi call sites in Search page chunk + zomaland php context"""
import re, glob

for f in sorted(glob.glob("_js/z_*.js")):
    if "Search" not in f and "search" not in f:
        continue
    s = open(f, "r", encoding="utf-8", errors="replace").read()
    print("== %s len=%d ==" % (f, len(s)))
    for kw in ["searchapi", "j5", "rnm", "entity_id", "applyFilter", "searchapi.php", "category"]:
        cnt = s.count(kw)
        if cnt:
            print("  kw %s x%d" % (kw, cnt))
            for mm in list(re.finditer(re.escape(kw), s))[:4]:
                i = mm.start()
                print("   ", s[max(0, i - 100):i + 130].replace("\n", " ")[:230])
                print("   ---")
print("\n== zomaland php context in main ==")
s = open("_js/z_main-8efa4cf644fa76389041.js", "r", encoding="utf-8", errors="replace").read()
for kw in ["make_payment", "pre_register", "payment_handler"]:
    i = s.find(kw)
    if i >= 0:
        print(kw, ":", s[max(0, i - 400):i + 400].replace("\n", " ")[:800], "\n")
print("done", flush=True)
