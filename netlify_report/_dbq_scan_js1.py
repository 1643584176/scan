# -*- coding: utf-8 -*-
"""扫 net_app.js:提取 database 功能相关端点与调用上下文"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. 所有 /.netlify/functions/* 端点
eps = sorted(set(re.findall(r'/\.netlify/functions/[A-Za-z0-9_\-]+', data)))
print('== functions endpoints (%d) ==' % len(eps))
for e in eps:
    print(' ', e)

# 2. database 相关关键词上下文(找 URL/调用模式)
print()
print('== database-* 关键词上下文 ==')
keys = ['database-query', 'database-info', 'database-branching', 'database-drivers',
        'database_studio', 'database-branch', 'database-settings']
for k in keys:
    idxs = [m.start() for m in re.finditer(re.escape(k), data)]
    print('\n-- %s (%d hits) --' % (k, len(idxs)))
    for i in idxs[:4]:
        ctx = data[max(0, i - 150):i + 150].replace('\n', ' ')
        print('   ...%s...' % ctx)

# 3. 含 netlifydb 或 neon 的完整字符串
print()
print('== netlifydb/neon 字符串 ==')
for m in sorted(set(re.findall(r'[A-Za-z0-9_\-\.]{0,40}(?:netlifydb|neon|storage_token)[A-Za-z0-9_\-\.]{0,60}', data))):
    print(' ', m[:140])
