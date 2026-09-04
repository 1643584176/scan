# -*- coding: utf-8 -*-
"""双 HAR 深度提取:B 访问 A 资源的响应、WS 参数、uid 头分布、响应体样本"""
import json

def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)['log']['entries']

A = load('C:/Users/tndc2/Desktop/www.figma.com.har')
B = load('C:/Users/tndc2/Desktop/www.figma.com2.har')

# 1. B HAR 中 x-figma-user-id 分布
print('=== B HAR 的 X-Figma-User-ID 分布 ===')
from collections import Counter
ids = Counter()
for e in B:
    hdrs = {h['name'].lower(): h['value'] for h in e['request']['headers']}
    ids[hdrs.get('x-figma-user-id', '(none)')] += 1
for k, v in ids.most_common():
    print('  %s x %d' % (k, v))

# 2. B 访问 A 资源的响应(B 会话请求 A 的端点)
print('\n=== B 请求中含 A 资源 key 的条目 ===')
akeys = ['IHt8kgtR3XmtqU5i8vz7p1', 'ee99ef1fda967d8a27a35f447c51ccdc77f9ee2a',
         '1666382703778278399', 'lk-']
for e in B:
    url = e['request']['url']
    if any(k in url for k in akeys) and 'www.figma.com' in url:
        body = e['request'].get('postData', {}).get('text', '')[:150]
        r = e['response']
        resp_txt = (r.get('content', {}).get('text') or '')[:300]
        print('  %s %s' % (e['request']['method'], url.split('www.figma.com')[1][:110]))
        print('    status=%d ct=%s' % (r['status'], r.get('content', {}).get('mimeType', '')))
        print('    body: %s' % body.replace('\n', ' '))
        print('    resp: %s' % resp_txt.replace('\n', ' ')[:250])

# 3. WS URL 参数
print('\n=== B HAR 的 WS URL ===')
for e in B:
    url = e['request']['url']
    if 'livegraph' in url or 'multiplayer' in url:
        print('  %s' % url[:220])

# 4. 关键响应体样本(数据结构)
print('\n=== 关键端点响应体样本 ===')
want = ['file_metadata', 'roles/team', 'ai_credits', 'mcp_usage', 'session/state', 'pricing/rates']
seen = set()
for e in B:
    url = e['request']['url']
    if not ('www.figma.com/api/' in url):
        continue
    if not any(w in url for w in want):
        continue
    path = url.split('www.figma.com')[1].split('?')[0]
    if path in seen:
        continue
    seen.add(path)
    r = e['response']
    resp_txt = (r.get('content', {}).get('text') or '')[:600]
    print('  %s' % path[:100])
    print('    status=%d %s' % (r['status'], resp_txt.replace('\n', ' ')[:400]))
