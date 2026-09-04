# -*- coding: utf-8 -*-
"""挖 agent-runner-file-delete 上下文:fileKey 来源/格式/agent-runner 家族"""
import re, glob, os

files = glob.glob(r'D:\scan\netlify_report\_js\*.js')
# 1. agent-runner 家族全部引用
print('==== agent-runner* 家族引用 ====')
for fn in files:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'agent-runner[^"\\\']*', data):
        print(fn.split('\\')[-1], '@', m.start(), ':', m.group(0)[:80])

# 2. agent-runner-file-delete 前后文(大窗口)
print()
print('==== agent-runner-file-delete 上下文 ====')
for fn in files:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    for m in re.finditer('agent-runner-file-delete', data):
        s = max(0, m.start() - 2500)
        e = min(len(data), m.end() + 2500)
        print('####', fn.split('\\')[-1], '@', m.start())
        print(data[s:e].replace('\n', ' '))
        print('=' * 80)
