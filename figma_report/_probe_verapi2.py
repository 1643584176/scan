# -*- coding: utf-8 -*-
"""考古版本写操作: main JS 里 save/restore/rename version 的 API URL 与 action"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# 1. version 写相关的 UI/action 关键词上下文
for kw in ['restoreVersion', 'restore_version', 'saveVersion', 'save_version', 'createVersion',
           'versionRestore', 'versions/restore', 'editVersion', 'renameVersion', 'versionDelete', 'deleteVersion']:
    hits = list(re.finditer(re.escape(kw), data))[:2]
    for h in hits:
        s = max(0, h.start() - 150)
        e = min(len(data), h.end() + 200)
        print(f'=== main {kw}@ {h.start()}:')
        print(f'   {data[s:e][:360]}')
        print()

# 2. 搜所有 chunk 里的 versions 写 URL (POST/PUT 模板)
print('===== chunk 扫描 versions 写 =====')
for pat in [r'(?:post|put|delete)[^;]{0,60}[/]api/versions[^"`]{0,60}',
            r'url`[^`]{0,80}versions[^`]{0,60}`']:
    n = 0
    for fn in sorted(os.listdir(JS)):
        if not fn.endswith('.min.js'):
            continue
        p = os.path.join(JS, fn)
        d = open(p, encoding='utf-8', errors='replace').read()
        for m in re.finditer(pat, d):
            s = max(0, m.start() - 100)
            e = min(len(d), m.end() + 100)
            print(f'{fn}: {d[s:e][:260]}')
            print()
            n += 1
            if n > 15:
                print('TRUNCATED')
                print('ALL DONE')
                sys.exit(0)
print('ALL DONE')
