# -*- coding: utf-8 -*-
# g7: 最终验证——经验库 4 文件结构 + figma 三文档存在
import io, os
kb = r'D:\scan\经验\全局经验\SQL注入经验库'
fr = r'D:\scan\figma_report'

def titles(path, pat='## '):
    c = io.open(path, encoding='utf-8', errors='replace').read()
    return [l for l in c.split('\n') if l.startswith(pat)]

print('=== 03-判读库 ===')
for t in titles(os.path.join(kb, '03-判读库.md')):
    print('  ', t)
print('=== 05-实战案例 ===')
for t in titles(os.path.join(kb, '05-实战案例.md'))[:9]:
    print('  ', t)
print('=== CHANGELOG ===')
for t in titles(os.path.join(kb, 'CHANGELOG.md')):
    print('  ', t)
print('=== 01 V6 check ===')
c = io.open(os.path.join(kb, '01-SQL入参矩阵.md'), encoding='utf-8').read()
print('  含静默宽容:', '批量端点静默宽容' in c)
print('=== figma 三文档 ===')
for f in ['Figma-SQL注入总账-2026-09-10.md', 'Figma-SQL请求解析源码汇总-2026-09-10.md', 'Figma-今日总结-2026-09-10.md']:
    p = os.path.join(fr, f)
    print('  %s  %d bytes  %s' % ('OK ' if os.path.exists(p) else 'MISS', os.path.getsize(p) if os.path.exists(p) else 0, f))
