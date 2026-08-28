# -*- coding: utf-8 -*-
"""梳理 e1507845(08-27) 未闭合实验: 提取所有实验编号与结论"""
import re, os, json

fp = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\e1507845\e1507845.jsonl'
with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

out = []
for line in lines:
    try:
        obj = json.loads(line)
    except Exception:
        continue
    if obj.get('role') != 'assistant':
        continue
    msg = obj.get('message', {})
    content = msg.get('content')
    if not isinstance(content, list):
        continue
    for item in content:
        if not isinstance(item, dict) or item.get('type') != 'text':
            continue
        t = item.get('text', '')
        if len(t) < 40:
            continue
        out.append(t.replace('\n', ' '))

with open(r'D:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('segments:', len(out))
