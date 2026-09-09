# -*- coding: utf-8 -*-
"""考古:订阅/收藏/intent mutation 文档串全文(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

for op in ["UpdateReportSubscriptionForNotifications", "UpdateReportSubscriptionForMetadata",
           "UpdateReportFavorite", "CreateReportIntentV2", "SaveReportIntent"]:
    for m in re.finditer(re.escape(op), data):
        # 找文档串形式(引号包裹的 \n 转义串)
        ctx = data[m.start():m.start() + 1500]
        if ctx.startswith(op) or "mutation" in ctx[:40]:
            # 尝试从最近的 " 或 : 开始找完整
            start = data.rfind('"', 0, m.start())
            seg = data[start:m.start() + 1500].replace("\\n", "\n")
            if "mutation" in seg[:500]:
                print(f"===== {op}")
                print(seg[:1200])
                print()
                break
