# -*- coding: utf-8 -*-
"""从会话历史中提取用户贴的 Figma scope 原文 (含 weavy 的消息)"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

p = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\c57b94b5\c57b94b5.jsonl'
for line in open(p, encoding='utf-8', errors='replace'):
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get('role') != 'user':
        continue
    c = o.get('message', {}).get('content', '')
    txt = ''
    if isinstance(c, str):
        txt = c
    elif isinstance(c, list):
        for part in c:
            if isinstance(part, dict):
                txt += part.get('text', '') or part.get('content', '') or ''
    if 'weavy' in txt.lower() or 'Weave' in txt:
        print('===== user msg =====')
        print(txt[:3000])
        print()
