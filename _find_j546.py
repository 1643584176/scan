# -*- coding: utf-8 -*-
"""查找 J546 捕获输出与今日进度相关文件"""
import os, re, datetime

roots = [r'F:\scan\skills\non-traditional-vuln-hunting', r'F:\scan\out', r'F:\scan\reports', r'F:\scan']
pat = re.compile(r'cap\d|resp\d|j546|j545|b64|spawn|mitm|forward', re.I)

print('=== 全工作区匹配 cap/resp/b64/mitm 的文件 ===')
seen = set()
for root in roots:
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过 __pycache__ 和 .venv
        if '__pycache__' in dirpath or '.venv' in dirpath or '.git' in dirpath:
            continue
        for f in filenames:
            if pat.search(f):
                p = os.path.join(dirpath, f)
                if p in seen: continue
                seen.add(p)
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d %H:%M')
                print(f'  [{mt}] {p}  ({os.path.getsize(p)} B)')

print()
print('=== 今日(08-29)修改/创建的所有脚本类文件 ===')
today = datetime.datetime(2026, 8, 29).timestamp()
for dirpath, dirnames, filenames in os.walk(r'F:\scan\skills\non-traditional-vuln-hunting'):
    if '__pycache__' in dirpath: continue
    for f in filenames:
        p = os.path.join(dirpath, f)
        if os.path.getmtime(p) >= today and f.endswith('.py'):
            mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M')
            print(f'  [{mt}] {f}')
