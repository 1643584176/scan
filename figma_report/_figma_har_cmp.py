# -*- coding: utf-8 -*-
"""双 HAR 交叉对比:账号 1643(A) vs 7294(B)
输出:各自 uid/端点/文件/团队 + A-B 差异矩阵
"""
import json
from collections import defaultdict

HARS = {'A1643': 'C:/Users/tndc2/Desktop/www.figma.com.har',
        'B7294': 'C:/Users/tndc2/Desktop/www.figma.com2.har'}

def parse(path):
    with open(path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    out = {'uid': None, 'team': None, 'endpoints': set(), 'files': set(),
           'posts': {}, 'methods': defaultdict(int), 'statuses': defaultdict(int)}
    for e in har['log']['entries']:
        req = e['request']
        url = req['url']
        m = req['method']
        out['methods'][m] += 1
        out['statuses'][e['response']['status']] += 1
        hdrs = {h['name'].lower(): h['value'] for h in req['headers']}
        if not out['uid'] and hdrs.get('x-figma-user-id'):
            out['uid'] = hdrs['x-figma-user-id']
        if not out['team'] and hdrs.get('x-figma-team-id'):
            out['team'] = hdrs['x-figma-team-id']
        # 仅 www.figma.com 的 API 端点
        if 'www.figma.com/api/' in url:
            path = url.split('www.figma.com')[1].split('?')[0]
            out['endpoints'].add((m, path))
            import re
            for fk in re.findall(r'[A-Za-z0-9]{16,22}', path):
                if len(fk) >= 16 and not fk.isdigit():
                    out['files'].add(fk)
        # 关键 POST body
        if req['method'] == 'POST' and 'www.figma.com' in url:
            pd = req.get('postData', {})
            body = (pd.get('text') or '')[:200]
            if body:
                key = (m, url.split('www.figma.com')[1].split('?')[0])
                if key not in out['posts']:
                    out['posts'][key] = body
    return out

A = parse(HARS['A1643'])
B = parse(HARS['B7294'])

print('=== 账号身份 ===')
print('A(1643): uid=%s team=%s' % (A['uid'], A['team']))
print('B(7294): uid=%s team=%s' % (B['uid'], B['team']))
print('A: 方法=%s 状态=%s' % (dict(A['methods']), dict(A['statuses'])))
print('B: 方法=%s 状态=%s' % (dict(B['methods']), dict(B['statuses'])))

print('\n=== 端点差异(B 没有的 A 端点) ===')
onlyA = A['endpoints'] - B['endpoints']
for m, p in sorted(onlyA):
    print('  %-6s %s' % (m, p[:110]))

print('\n=== 端点差异(A 没有的 B 端点) ===')
onlyB = B['endpoints'] - A['endpoints']
for m, p in sorted(onlyB):
    print('  %-6s %s' % (m, p[:110]))

print('\n=== 文件 key 差异 ===')
print('A files:', sorted(A['files']))
print('B files:', sorted(B['files']))
print('only A:', sorted(A['files'] - B['files']))
print('only B:', sorted(B['files'] - A['files']))

print('\n=== B 的 POST body(A 没有的) ===')
for (m, p), body in sorted(B['posts'].items()):
    if (m, p) not in A['posts']:
        print('  %s %s' % (m, p[:100]))
        print('    %s' % body[:200])
