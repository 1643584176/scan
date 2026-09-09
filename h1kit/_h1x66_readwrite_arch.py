# -*- coding: utf-8 -*-
"""考古:读类写 mutation 文档串(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

for op in ["DetectSensitiveData", "ExportReportPdf", "CheckReportCampaignInclusion", "PingPageActivity"]:
    hits = list(re.finditer(re.escape(op), data))
    print(f"== {op}: {len(hits)} hits")
    for m in hits[:4]:
        start = data.rfind('"', 0, m.start())
        seg = data[start:m.start() + 1300].replace("\\n", "\n")
        if re.search(r"(mutation|query|fragment)", seg[:400], re.I):
            print(seg[:1100])
            print("---")
            break
