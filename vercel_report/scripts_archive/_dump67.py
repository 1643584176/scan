# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
txt = open(r'D:\scan\v67_run.log', encoding='utf-8', errors='replace').read()
# 提取所有 "data" 字段 (stream stdout) 合并输出
for m in __import__('re').finditer(r'\{"data":"((?:[^"\\]|\\.)*)","stream":"stdout"\}', txt):
    s = m.group(1).encode().decode('unicode_escape')
    print(s, end='')
