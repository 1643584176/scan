# -*- coding: utf-8 -*-
"""本地: 找签名 header 名 + WrapUnary.func1 缺头分支"""
import re

d = open("_sandbox_init_new.bin", "rb").read()

# 1) 找 "missing signature header" 字符串位置
idx = d.find(b"missing signature header")
print("missing sig string @", hex(idx) if idx >= 0 else "NOT FOUND")

# 2) 找 signature 相关字符串 (header 名候选)
for m in re.finditer(rb"[A-Za-z0-9\-_:]{4,40}signature[A-Za-z0-9\-_:]{0,30}", d):
    s = m.group()
    print("SIGSTR:", s.decode("latin1"))
