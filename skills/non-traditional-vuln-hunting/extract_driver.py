# -*- coding: utf-8 -*-
"""从 3d4619a8 提取完整 Vercel API 驱动脚本"""
import os, re, json

fp = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\3d4619a8\3d4619a8.jsonl'
with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

out = []
# 提取代码块内容
for m in re.finditer(r'```(?:python)?\s*\n(.*?)```', content, re.S):
    out.append('=' * 20)
    out.append(m.group(1)[:3000])

with open(r'D:\scan\skills\non-traditional-vuln-hunting\vercel_driver_recovered.py.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('blocks:', len(out))
