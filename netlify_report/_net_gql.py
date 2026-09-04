# -*- coding: utf-8 -*-
"""Netlify:搜 bundle 中 GraphQL 端点"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
for f in sorted(os.listdir(jsdir)):
    if not f.endswith('.js'):
        continue
    txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()
    hits = 0
    for kw in ['graphql', 'GraphQL', 'graphiql']:
        for m in re.finditer(re.escape(kw), txt):
            i = m.start()
            ctx = txt[max(0, i - 400): i + 400]
            # 找 URL/路径
            urls = re.findall(r'["\'`]((?:https?://[^"\'`\s]+|/[a-zA-Z0-9_\-${}/.]*(?:graphql|GraphQL)[a-zA-Z0-9_\-${}/.?=&%]*))["\'`]', ctx)
            if urls:
                print('[%s] %s:' % (f.replace('net_', '').replace('.js', ''), kw))
                for u in urls[:3]:
                    print('  url:', u[:150])
                hits += 1
                break
    if hits:
        continue
# 再精确找 url 构造
print('--- url 构造 ---')
for f in sorted(os.listdir(jsdir)):
    if not f.endswith('.js'):
        continue
    txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'(?:url|endpoint|uri)\s*[:=]\s*["\'`]([^"\'`]*(?:graphql|GraphQL)[^"\'`]*)', txt):
        print('[%s]' % f.replace('net_', '').replace('.js', ''))
        print('  ', m.group(1)[:200])
