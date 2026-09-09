# -*- coding: utf-8 -*-
"""考古:AddReportParticipant + 参与者相关 mutation(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. AddReportParticipant 文档串
for op in ["AddReportParticipant", "acceptReportCollaboratorInvitation", "reportCollaboratorInvitation",
           "removeReportParticipant", "RemoveReportParticipant"]:
    hits = list(re.finditer(re.escape(op), data))
    print(f"== {op}: {len(hits)} hits")
    for m in hits[:3]:
        start = data.rfind('"', 0, m.start())
        seg = data[start:m.start() + 1200].replace("\\n", "\n")
        # 只打印文档串(含 mutation/query 的)
        if re.search(r"(mutation|query|fragment)", seg[:400], re.I):
            print(seg[:1000])
            print("---")
            break

# 2. 找 collaborator/participant 相关全部 mutation 名
print("== participant/collaborator 相关 mutation:")
for m in re.finditer(r"mutation\s+([A-Za-z0-9_]*[Pp]articipant[A-Za-z0-9_]*|[A-Za-z0-9_]*[Cc]ollaborator[A-Za-z0-9_]*)", data):
    print("   ", m.group(1))
