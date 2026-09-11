# -*- coding: utf-8 -*-
"""挖 JS 2: diff_version 计算(N.C2) + fileVersion 来源 + Q 调用者"""
import os, io

JS = r'D:\scan\figma_report\_js'
F = 'figma_app-main.js'
t = io.open(os.path.join(JS, F), encoding='utf-8', errors='ignore').read()

def hits(term, before=400, after=900, cap=10):
    i = 0; n = 0
    while True:
        i = t.find(term, i)
        if i < 0: break
        n += 1
        print('=' * 16, term, '| hit', n, '| pos', i)
        print(t[max(0, i - before):i + after].replace('\n', ' ')[:1300])
        print()
        i += len(term)
        if n >= cap:
            print('... (truncated)')
            break

hits('Error viewing what\'s changed', cap=5)
hits('C2:()', before=100, after=500, cap=8)
hits('C2=', before=60, after=400, cap=8)
hits('fileVersion:', before=300, after=500, cap=6)
hits('fileVersion=', before=300, after=500, cap=6)
print('DONE2')
