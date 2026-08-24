# -*- coding: utf-8 -*-
"""列出业务函数中非 proto/connect 框架的部分"""
import re

lines = open("_biz_all.txt", encoding="utf-8", errors="replace").read().splitlines()
for ln in lines:
    if re.search(r"gen/spawn\.|connect\.", ln):
        continue
    print(ln)
