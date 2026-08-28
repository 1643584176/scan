# -*- coding: utf-8 -*-
"""解析 JSONL 提取代码块"""
import os, json

fp = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\3d4619a8\3d4619a8.jsonl'
out = []
with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        msg = obj.get('message', {})
        content = msg.get('content')
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get('type') == 'text':
                t = item.get('text', '')
                # 代码块
                import re
                for m in re.finditer(r'```(?:python)?\s*\n(.*?)```', t, re.S):
                    out.append('=' * 20)
                    out.append(m.group(1)[:4000])

with open(r'D:\scan\skills\non-traditional-vuln-hunting\vercel_driver_recovered.py.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('blocks:', len(out))
