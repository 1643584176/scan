# -*- coding: utf-8 -*-
"""ExportLifetimeReports 调用上下文考古(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. 文档串全文(操作名 ExportLifetimeReports / ExportLifeTimeReportsMutation)
for op in ["ExportLifetimeReports", "ExportLifeTimeReportsMutation"]:
    for m in re.finditer(re.escape(op), data):
        start = max(0, m.start() - 200)
        ctx = data[start:m.start() + 1200].replace("\\n", "\n")
        print(f"===== ctx for {op} @ {m.start()}")
        print(ctx[:1300])
        print()

# 2. mutation 字段名:找 exportLifetimeReports(小写驼峰)定义与调用
for m in re.finditer(r"exportLifetimeReports", data):
    start = max(0, m.start() - 150)
    ctx = data[start:m.start() + 900].replace("\\n", "\n")
    print(f"===== exportLifetimeReports @ {m.start()}")
    print(ctx[:1000])
    print()
