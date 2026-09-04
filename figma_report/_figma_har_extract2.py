# -*- coding: utf-8 -*-
"""Figma HAR 第二轮提取:认证机制 + WS 连接 + 关键请求样本"""
import json
from collections import Counter, defaultdict

HAR = 'C:/Users/tndc2/Desktop/www.figma.com.har'
with open(HAR, 'r', encoding='utf-8') as f:
    har = json.load(f)
entries = har['log']['entries']
print('entries:', len(entries))

# 1. 完整认证头(cookie 数组 + headers)
print('\n== 认证机制(第一个 API 请求) ==')
for e in entries:
    url = e['request']['url']
    if '/api/' in url and e['request']['method'] in ('GET', 'POST'):
        hdrs = {h['name'].lower(): h['value'] for h in e['request']['headers']}
        print('URL:', url[:100])
        print('  headers:')
        for k, v in hdrs.items():
            if k in ('cookie', 'authorization', 'x-figma-token', 'x-token', 'x-figma-session-id', 'x-figma-user-id', 'x-figma-client-version'):
                print('    %s: %s' % (k, v[:120]))
        if e['request'].get('cookies'):
            print('  cookies[]:', [(c['name'], c['value'][:50]) for c in e['request']['cookies']])
        print('  queryString:', e['request'].get('queryString', []))
        break

# 2. 所有 request.cookies 出现过的条目数
n_cookie_arr = 0
cookie_names = set()
for e in entries:
    if e['request'].get('cookies'):
        n_cookie_arr += 1
        for c in e['request']['cookies']:
            cookie_names.add(c['name'])
print('\n带 request.cookies 数组的条目:', n_cookie_arr)
print('cookie 名:', cookie_names)

# 3. WS 连接(101)
print('\n== WebSocket 条目 ==')
for e in entries:
    if e['response']['status'] == 101 or e['request']['method'] == 'GET' and 'livegraph' in e['request']['url']:
        print('  WS URL:', e['request']['url'][:200])

# 4. 关键 POST body 样本
print('\n== 关键 POST body 样本 ==')
interesting = ['ai_chat', 'cortex', 'files/create', 'files/batch', 'realtime_token', 'published_package', 'folders']
seen = set()
for e in entries:
    url = e['request']['url']
    if any(k in url for k in interesting) and e['request']['method'] == 'POST':
        pd = e['request'].get('postData', {})
        body = pd.get('text', '')[:300] if pd else ''
        key = url.split('/api/')[1][:60]
        if key in seen:
            continue
        seen.add(key)
        print('  POST %s' % url[:110])
        print('    mimeType:', pd.get('mimeType', ''))
        print('    body:', body.replace('\n', ' ')[:250])
