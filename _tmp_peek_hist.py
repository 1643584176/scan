# -*- coding: utf-8 -*-
import json, re, sys

p = sys.argv[1]
lines = open(p, encoding='utf-8').readlines()
kws = ['org-', '@gmail', '@qq', 'invit', 'member', 'transfer', '账号', '帐号', 'B 账号', 'b账号', '第二个']
for line in lines:
    try:
        j = json.loads(line)
    except Exception:
        continue
    if j.get('role') != 'user':
        continue
    c = j.get('message', {}).get('content', '')
    if isinstance(c, list):
        c = ' '.join(str(x.get('text', '')) for x in c if isinstance(x, dict))
    c = str(c)
    hits = [k for k in kws if k.lower() in c.lower()]
    if hits and len(c) > 30:
        # 只打印包含关键上下文片段
        for k in hits:
            for m in re.finditer(re.escape(k), c, re.IGNORECASE):
                s = max(0, m.start() - 200)
                print('[' + k + ']', c[s:m.end() + 300].replace('\n', ' ')[:520])
                print('---')
                break
