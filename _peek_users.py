# -*- coding: utf-8 -*-
import json
for line in open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\0cd3bdc9\0cd3bdc9.jsonl', encoding='utf-8'):
    try:
        j = json.loads(line)
    except Exception:
        continue
    if j.get('role') == 'user':
        c = j.get('message', {}).get('content', '')
        if isinstance(c, list):
            c = ' '.join(str(x.get('text', '')) for x in c if isinstance(x, dict))
        if c:
            print(str(c)[:500].replace('\n', ' | '))
            print('---')
