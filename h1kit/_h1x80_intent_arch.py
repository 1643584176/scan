# -*- coding: utf-8 -*-
"""考古:ReportIntent 创建/查询结构 + id 形态(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

for op in ["CreateReportIntentV2", "SaveReportIntent", "report_intents", "ReportIntentV2", "submitReportIntent"]:
    hits = list(re.finditer(re.escape(op), data))
    print(f"== {op}: {len(hits)}")
    for m in hits[:3]:
        start = data.rfind('"', 0, m.start())
        seg = data[start:m.start() + 800].replace("\\n", "\n")
        if "mutation" in seg[:200]:
            print(seg[:700])
            print("---")
            break
