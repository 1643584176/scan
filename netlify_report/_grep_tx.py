# -*- coding: utf-8 -*-
import json, re

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
    if isinstance(msg, list):
        parts = []
        for x in msg:
            if isinstance(x, dict):
                if x.get('type') == 'text':
                    parts.append(x.get('text', ''))
        txt = ' '.join(parts)
    else:
        txt = str(msg)
    txt = txt.strip().replace('\n', ' ')
    if not txt:
        continue
    if 'Version: 2024.3.5' in txt or 'selected_codes' in txt or 'attached_files' in txt or '<code>' in txt:
        continue
    print(i, '|', txt[:200])
