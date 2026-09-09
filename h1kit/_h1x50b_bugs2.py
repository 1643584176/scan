# -*- coding: utf-8 -*-
"""考古 /bugs 页面:program_states/reported_to_team/subject 参数构造点"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

def dump(i, pre=1200, post=900, label='', limit=2100):
    print('=' * 70)
    print(label, '@', i, ':')
    print(t[max(0, i-pre):i+post][:limit])

for pat in [r'program_states', r'reported_to_team', r'subject[=:]user', r'`/bugs`', r'"bugs"', r'subject[=:]\s*`?\$?\{']:
    idxs = [m.start() for m in re.finditer(pat, t)]
    print(pat, 'count:', len(idxs))
    for i in idxs[:4]:
        dump(i, 900, 700, pat)
