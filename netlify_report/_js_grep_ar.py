# -*- coding: utf-8 -*-
import re
t = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
print('len:', len(t))
for name in ['agent-runner-file-upload', 'fileKey']:
    hits = [m.start() for m in re.finditer(re.escape(name), t)]
    print(name, 'hits:', len(hits))
seen = set()
for m in re.finditer(r'agent-runner[a-z-]*', t):
    key = m.group(0)
    if key in seen:
        continue
    seen.add(key)
    s = max(0, m.start() - 250)
    print('---', key)
    print(t[s:m.end() + 300].replace('\n', ' ')[:520])
