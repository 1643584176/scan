# -*- coding: utf-8 -*-
import json

f = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\92f41401\92f41401.jsonl',
         encoding='utf-8', errors='replace')
lines = f.readlines()
for i, ln in enumerate(lines):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    if o.get('role') != 'user':
        continue
    try:
        msg = o['message']['content']
    except Exception:
        continue
    if not isinstance(msg, list):
        continue
    texts = []
    for x in msg:
        if isinstance(x, dict) and x.get('type') == 'text':
            texts.append(x.get('text', ''))
    if not texts:
        continue
    # 最后一块 text(真正的 user query)
    last = texts[-1].strip().replace('\n', ' ')
    if not last or last.startswith('<'):
        continue
    print(i, '|', last[:150])
