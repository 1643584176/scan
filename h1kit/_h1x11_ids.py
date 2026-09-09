# -*- coding: utf-8 -*-
"""h1x11: 从存档文件提取已知报告编号(邮件 duplicate 通知样本)"""
import sys, io, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ids = set()
for f in glob.glob(r'D:\scan\**\*.md', recursive=True) + glob.glob(r'D:\scan\*.md'):
    try:
        t = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'(?:#|reports?/)(\d{5,8})', t):
        ids.add(m.group(1))
for f in glob.glob(r'D:\scan\figma_report\*.md'):
    try:
        t = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'(?:#|reports?/)(\d{5,8})', t):
        ids.add(m.group(1))
print('found ids:', sorted(ids, key=int))
