# -*- coding: utf-8 -*-
"""考古:执行器类 mutation(InvokeExploitAgent/CodeValidation/CveRequest)(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

for op in ["InvokeExploitAgent", "InvokeCodeValidationAgent", "InvokeLinearAgent", "CreateCveRequest"]:
    hits = list(re.finditer(re.escape(op), data))
    print(f"===== {op}: {len(hits)}")
    for m in hits[:4]:
        start = data.rfind('"', 0, m.start())
        seg = data[start:m.start() + 1000].replace("\\n", "\n")
        if re.search(r"(mutation|query|fragment)", seg[:400], re.I):
            print(seg[:900])
            print("---")
            break
    # 调用上下文(非文档串)
    for m in hits[:3]:
        ctx = data[max(0, m.start() - 200):m.start() + 300].replace("\n", " ")
        if "mutation" not in ctx[:200] and "Document" not in ctx[:200]:
            print("CALL>>>", ctx[:450])
            print("~~~")
            break
