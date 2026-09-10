# -*- coding: utf-8 -*-
"""考古:collaborator invitation token 来源/链接格式(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. acceptReportCollaboratorInvitation 调用上下文
for m in re.finditer(r"acceptReportCollaboratorInvitation", data):
    ctx = data[m.start() - 500:m.start() + 300]
    if "mutation" not in ctx:
        print("CALL>>>", ctx[:700].replace("\n", " "))
        print("---")
        break

# 2. token 相关:collaborator invitation 链接/路由
for pat in [r"collaborators?[^\"']{0,60}(invit|token)[^\"']{0,60}", r"invitation[^\"']{0,80}token"]:
    for m in re.finditer(pat, data, re.I):
        print("PAT>>>", m.group(0)[:200])
