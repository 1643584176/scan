# -*- coding: utf-8 -*-
"""考古:reportPdfExportTypes 定义(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

for m in re.finditer(r"reportPdfExportTypes\s*[:=]", data):
    ctx = data[m.start():m.start() + 400]
    print(ctx[:400])
    print("===")
    break

# 也搜 pdf 导出相关常量
for m in re.finditer(r"(pdfTypes|PDF_TYPES|pdf_type|PdfExport)", data):
    pass
# 在可能的小 chunk 里找:含 "PDF export" 文案的上下文往前找定义
for m in re.finditer(r"PDF export has been queued", data):
    ctx = data[m.start() - 2500:m.start()]
    idx = ctx.rfind("reportPdfExportTypes")
    if idx >= 0:
        print("DEF>>>", ctx[idx:idx + 600])
        break
