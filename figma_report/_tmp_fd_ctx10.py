# -*- coding: utf-8 -*-
"""挖 JS 9: release_manifest 来源(客户端版本头真值) + cortex 相关"""
import os, io

JS = r'D:\scan\figma_report\_js'
terms = ['release_manifest_git_commit', 'release_manifest', 'release_git_tag', 'releaseManifest']

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
            if n <= 8:
                print('=' * 18, f, '|', term, '| hit', n, '| pos', i)
                print(t[max(0, i - 350):i + 450].replace('\n', ' ')[:1050])
                print()
            i += len(term)
        if n:
            print('   (total %s in %s: %d)' % (term, f, n))
print('DONE9')
