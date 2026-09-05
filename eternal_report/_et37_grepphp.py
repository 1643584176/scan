# -*- coding: utf-8 -*-
"""grep zomato bundles for searchapi.php + param context"""
import re, os, glob

for f in sorted(glob.glob("_js/z_*.js")):
    s = open(f, "r", encoding="utf-8", errors="replace").read()
    hits = list(re.finditer(r"searchapi\.php", s, re.I))
    if hits:
        print("== %s (%d hits) ==" % (f, len(hits)))
        for m in hits[:6]:
            i = m.start()
            print("   ...%s..." % s[max(0, i - 150):i + 250].replace("\n", " ")[:400])
            print("   ---")

print("\n== /webapi/ refs ==")
for f in sorted(glob.glob("_js/z_*.js")):
    s = open(f, "r", encoding="utf-8", errors="replace").read()
    for m in list(re.finditer(r"webapi[^\"']{0,80}", s))[:10]:
        i = m.start()
        print("%s: %s" % (f.split("/")[-1][:30], s[max(0, i - 60):i + 120].replace("\n", " ")[:180]))
print("done", flush=True)
