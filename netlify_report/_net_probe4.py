# -*- coding: utf-8 -*-
"""Netlify 侦察 4:从 bundle 提取 API 端点"""
import os, re, json

jsdir = r'D:\scan\netlify_report\_js'
all_txt = ''
for f in os.listdir(jsdir):
    if f.endswith('.js'):
        all_txt += open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()

print('total chars:', len(all_txt))

# 1. API 路径
paths = set()
for m in re.finditer(r'["\'`](/api/v\d/[a-zA-Z0-9_\-/{}$.:]+)["\'`]', all_txt):
    p = m.group(1)
    # 模板化简化
    paths.add(p[:120])
print('\n=== API 路径(前 60)===')
for p in sorted(paths)[:60]:
    print(' ', p)

# 2. GraphQL
print('\n=== GraphQL 相关 ===')
for kw in ['graphql', 'graphiql', 'gql']:
    for m in re.finditer(kw, all_txt):
        i = m.start()
        ctx = all_txt[max(0, i - 80): i + 120].replace('\n', ' ')
        if 'graphql' in ctx.lower() and ('endpoint' in ctx.lower() or 'url' in ctx.lower() or 'http' in ctx.lower()):
            print('  ', ctx[:200])
        break

# 3. 偏门关键词
print('\n=== 偏门关键词 ===')
for kw in ['private', 'internal', 'admin', 'beta', 'legacy', 'deprecated', 'hidden', 'debug', 'staging', 'preview']:
    hits = [m.start() for m in re.finditer(r'"([^"]*' + kw + r'[^"]*)"', all_txt)][:5]
    if hits:
        print('[%s]' % kw)
        for h in hits[:3]:
            print('   ', all_txt[max(0, h - 60): h + 90].replace('\n', ' ')[:150])
