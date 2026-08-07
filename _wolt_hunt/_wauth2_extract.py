# -*- coding: utf-8 -*-
"""从 consumer JS 提取 wauth2 相关端点与流程"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILES = ["js/18254-461b29196ba27e1e.js",
         "js/98229-16c7ebd6dbace978.js",
         "js/app-12aee142b7eb4dbb.js"]

for f in FILES:
    data = open(f, encoding="utf-8", errors="replace").read()
    print("#" * 20, f, len(data))
    # 1. 含 wauth2 的字符串字面量
    for m in re.finditer(r'"([^"]{0,300}wauth2[^"]{0,300})"', data):
        s = m.group(1)
        print("  S:", s[:260])
    # 2. 路径拼接模式: "/v1/wauth2/" 或 "wauth2/"
    for m in re.finditer(r'[/]v1/wauth2/[A-Za-z0-9_\-/\.\$\{]*', data):
        print("  P:", m.group(0)[:200])
    print()
