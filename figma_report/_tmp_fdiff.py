# -*- coding: utf-8 -*-
"""搜 file_diff / checkpoint_diff 在文档与经验库里的踪迹(定收口状态)"""
import os, io, re

for fn in [r'D:/scan/figma_report/Figma-SQL注入总账-2026-09-10.md',
           r'D:/scan/figma_report/Figma-SQL请求解析源码汇总-2026-09-10.md',
           r'D:/scan/figma_report/Figma-今日总结-2026-09-10.md',
           r'D:/scan/经验/全局经验/SQL注入经验库/01-SQL入参矩阵.md',
           r'D:/scan/经验/全局经验/SQL注入经验库/03-判读库.md',
           r'D:/scan/经验/全局经验/SQL注入经验库/05-实战案例.md',
           r'D:/scan/经验/全局经验/SQL注入经验库/CHANGELOG.md']:
    if not os.path.exists(fn):
        print('MISSING', fn)
        continue
    txt = io.open(fn, encoding='utf-8', errors='ignore').read()
    lines = txt.split('\n')
    print('#' * 20, os.path.basename(fn))
    hit = False
    for i, ln in enumerate(lines):
        if re.search(r'file_diff|checkpoint|from_file_version', ln, re.I):
            hit = True
            print('%4d| %s' % (i + 1, ln.strip()[:170]))
    if not hit:
        print('   (0 hits)')
