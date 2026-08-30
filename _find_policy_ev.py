# -*- coding: utf-8 -*-
"""搜历史创建响应中的 networkPolicy 证据 + 本地文档"""
import os, re

# 1. 搜 out/reports 里创建响应含 networkPolicy 的
for root in [r'F:\scan\skills\non-traditional-vuln-hunting', r'F:\scan\out', r'F:\scan\reports']:
    for dirpath, dirnames, filenames in os.walk(root):
        if '__pycache__' in dirpath: continue
        for f in filenames:
            if not f.endswith(('.txt', '.json', '.py')): continue
            p = os.path.join(dirpath, f)
            try:
                txt = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            for m in re.finditer(r'networkPolicy.{0,200}', txt):
                print('%s: %s' % (p, m.group(0)[:200]))
                print()
