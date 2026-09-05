# -*- coding: utf-8 -*-
import os, re, glob
base = r"F:\scan\neon_report"
# list md files mentioning the new surfaces
kws = ["ai_gateway", "AI Gateway", "nak_live", "functions", "storage", "credentials",
       "reveal", "object storage", "presign", "data-api", "Data API"]
for f in sorted(glob.glob(base + r"\*.md")):
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    hit = [k for k in kws if k.lower() in txt.lower()]
    if hit:
        print(os.path.basename(f), "->", hit[:6])
