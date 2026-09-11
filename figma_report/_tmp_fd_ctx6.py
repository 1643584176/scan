# -*- coding: utf-8 -*-
"""挖 JS 6: checkpoint_token/checkpointToken 用法 + chkpt + 475210 定义形态"""
import os, io

JS = r'D:\scan\figma_report\_js'

def scan(terms, cap=15, before=300, after=800):
    for f in sorted(os.listdir(JS)):
        if not f.endswith('.js'):
            continue
        try:
            t = io.open(os.path.join(JS, f), encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        for term in terms:
            i = 0; n = 0
            while True:
                i = t.find(term, i)
                if i < 0: break
                n += 1
                print('=' * 18, f, '|', term, '| hit', n, '| pos', i)
                print(t[max(0, i - before):i + after].replace('\n', ' ')[:1200])
                print()
                i += len(term)
                if n >= cap:
                    print('... (truncated)')
                    break

scan(['checkpoint_token', 'checkpointToken', 'chkpt'], cap=12)
print('DONE6')
