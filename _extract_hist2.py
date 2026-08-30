# -*- coding: utf-8 -*-
"""提取历史 transcript 中 30001/30002/j65/j77/j76 的完整上下文"""
import json, sys

path = r'C:\Users\lbb.LAPTOP-LU4P5L6T\.qoder\cache\projects\scan-dcb95ef8\conversation-history\04936518\04936518.jsonl'
kw = ['30001', '30002', 'j65', 'j77', 'j76', 'spawn.SpawnRequest', '免签', 'Kill', 'fd7', 'fd8']
out = []
with open(path, encoding='utf-8') as f:
    lines = f.readlines()
    for i, ln in enumerate(lines):
        if not any(k in ln for k in kw):
            continue
        try:
            d = json.loads(ln)
            texts = [c.get('text', '') for c in d['message']['content'] if c.get('type') == 'text']
            for t in texts:
                if any(k in t for k in kw):
                    out.append('LINE %d ROLE %s' % (i, d['role']))
                    out.append(t[:1500])
                    out.append('---')
        except Exception as e:
            out.append('err %d %s' % (i, e))

sys.stdout.reconfigure(encoding='utf-8')
print('\n'.join(out[:120]))
