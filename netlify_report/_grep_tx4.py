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
    for x in msg:
        if not (isinstance(x, dict) and x.get('type') == 'text'):
            continue
        t = x.get('text', '').strip()
        if t.startswith('<ide_context>') or t.startswith('<selected_codes>') or t.startswith('<attached_files>') or t.startswith('<user_memories>'):
            continue
        if not t:
            continue
        t2 = t.replace('\n', ' ')
        print(i, '|', t2[:200])
        print('---')
