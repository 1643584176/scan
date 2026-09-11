# -*- coding: utf-8 -*-
"""ctx13: JS 全量搜 file_diff 子路径 + checkpoint 端点 + signed_url 处理"""
import os, io

JS = r'D:\scan\figma_report\_js'
terms = ['file_diff', 'checkpoint_diff', 'signed_url', 'checkpoint_token']

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
            if n <= 6:
                print('=' * 12, f, '|', term, '| #', n, '| pos', i)
                print(t[max(0, i - 200):i + 260].replace('\n', ' ')[:460])
                print()
            i += len(term)
        if n:
            print('   (total %s in %s: %d)' % (term, f, n))
print('DONE13')
