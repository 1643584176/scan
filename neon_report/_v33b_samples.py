# -*- coding: utf-8 -*-
"""V33b: sample context around api/v2 refs to learn the path format"""
import re, os

ROOT = r"F:\scan\neon_report\_js"
targets = []
for dirpath, _, names in os.walk(ROOT):
    for n in names:
        if n.endswith(".js"):
            targets.append(os.path.join(dirpath, n))

for f in targets[:6]:
    s = open(f, encoding="utf-8", errors="replace").read()
    idxs = [m.start() for m in re.finditer(r"api/v2|/v2/|apiVersion|V2", s)][:8]
    print("=" * 20, f)
    for i in idxs:
        print("   ...%s..." % s[max(0, i - 120):i + 120].replace("\n", " "))
