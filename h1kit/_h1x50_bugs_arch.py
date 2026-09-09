# -*- coding: utf-8 -*-
"""考古 bugs 页面 URL 构造:bugs.json / subject / substates[] 的生成代码"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

Q = chr(39)
DQ = chr(34)

def dump(i, pre=1500, post=800, label=''):
    print('=' * 70)
    print(label, '@', i, ':')
    print(t[max(0, i-pre):i+post][:2300])

# 1. bugs.json 字符串
idxs = [m.start() for m in re.finditer(r'bugs\.json', t)]
print('bugs.json count:', len(idxs))
for i in idxs[:3]:
    dump(i, 1500, 500, 'bugs.json')

# 2. subject= 参数构造('subject=' + x 或 subject:)
for pat in [r'subject=' + Q + r'\+', r'subject[=:]', r'"subject"', Q + 'subject' + Q]:
    idxs2 = [m.start() for m in re.finditer(pat, t)]
    print(pat, 'count:', len(idxs2))
    for i in idxs2[:2]:
        dump(i, 800, 600, 'subject')

# 3. 'user' 与 'all' 等 subject 值候选:找 params.subject 或 setSubject
for pat in [r'setSubject', r'subject[=:]["\']all', r'params\.subject']:
    idxs3 = [m.start() for m in re.finditer(pat, t)]
    print(pat, 'count:', len(idxs3))
    for i in idxs3[:2]:
        dump(i, 600, 600, 'setSubject')
