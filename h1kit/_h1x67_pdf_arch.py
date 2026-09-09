# -*- coding: utf-8 -*-
"""考古:ExportReportPdf 前端调用上下文 + pdf_type 合法值(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. pdf_type 值域:找 pdf_type: "xxx" 或 pdf_type:"xxx"
vals = set()
for m in re.finditer(r'pdf_type\s*:\s*["\']([^"\']+)["\']', data):
    vals.add(m.group(1))
print("pdf_type 字面值:", vals)

# 2. exportReportPdf 调用点附近的变量(找 variables 构造)
for m in re.finditer(r'[Ee]xportReportPdf', data):
    ctx = data[m.start() - 300:m.start() + 300]
    if "mutation" not in ctx and ("pdf_type" in ctx or "email" in ctx or "redact" in ctx):
        print("CTX>>>", ctx[:500].replace("\n", " "))
        print("---")
