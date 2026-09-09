# -*- coding: utf-8 -*-
"""mermaid 配置/版本考古(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()
with open(r"D:\scan\h1kit\_h1x4_vendor.js", "r", encoding="utf-8", errors="replace") as f:
    vendor = f.read()

for name, d in [("app", data), ("vendor", vendor)]:
    print(f"########## {name} ##########")
    for kw in ["securityLevel", "mermaid.initialize", "startOnLoad", "htmlLabels", "flowchart", "theme:",
               '"mermaid"', "'mermaid'", "svgContent", "mermaidAPI", "parse("]:
        c = d.count(kw)
        if c:
            print(f"  {kw}: {c}")
    # securityLevel 上下文
    for m in list(re.finditer(r"securityLevel", d))[:4]:
        ctx = d[max(0, m.start() - 200):m.start() + 200]
        print("  SL ...", ctx[:380].replace("\n", " "))
    print()
