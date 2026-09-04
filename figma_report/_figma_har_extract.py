# -*- coding: utf-8 -*-
"""Figma HAR 分析:提取认证信息 + 端点清单 + 请求模式
输入:C:/Users/tndc2/Desktop/www.figma.com.har (338MB,账号1643)
输出:figma_report/_figma_har_analysis.txt + _figma_creds.txt(cookie)
"""
import json, os
from collections import Counter, defaultdict

HAR = 'C:/Users/tndc2/Desktop/www.figma.com.har'
OUT = 'D:/scan/figma_report/_figma_har_analysis.txt'
CRED = 'D:/scan/figma_report/_figma_creds.txt'

print('loading HAR...')
with open(HAR, 'r', encoding='utf-8') as f:
    har = json.load(f)
entries = har['log']['entries']
print('entries:', len(entries))

lines = []
def log(s=''):
    lines.append(s)
    print(s)

# 1. 方法/状态统计
methods = Counter(e['request']['method'] for e in entries)
statuses = Counter(e['response']['status'] for e in entries)
log('== 方法统计 ==')
for k, v in methods.most_common():
    log('  %-8s %d' % (k, v))
log('== 状态统计 ==')
for k, v in statuses.most_common():
    log('  %-8s %d' % (k, v))

# 2. 主机分布
hosts = Counter()
for e in entries:
    try:
        hosts[e['request']['url'].split('/')[2]] += 1
    except Exception:
        pass
log('== 主机分布 ==')
for k, v in hosts.most_common():
    log('  %s %d' % (k, v))

# 3. 端点清单(去重,按方法+路径)
paths = defaultdict(set)
for e in entries:
    url = e['request']['url']
    try:
        parts = url.split('/')
        host = parts[2]
        path = '/' + '/'.join(parts[3:]).split('?')[0]
    except Exception:
        continue
    if host in ('www.figma.com',):
        paths[(e['request']['method'], path[:120])].add(url.split('?')[1][:80] if '?' in url else '')
log('\n== www.figma.com 端点(方法+路径) ==')
for (m, p), qs in sorted(paths.items()):
    log('  %-7s %s' % (m, p))

# 4. 认证信息收集
cookies = {}
figma_headers = defaultdict(set)
for e in entries:
    for h in e['request']['headers']:
        n = h['name'].lower()
        if n == 'cookie':
            for c in h['value'].split(';'):
                c = c.strip()
                if '=' in c:
                    k, v = c.split('=', 1)
                    cookies.setdefault(k, set()).add(v[:40])
        elif n.startswith('x-figma') or n in ('authorization', 'x-token'):
            figma_headers[n].add(h['value'][:80])

log('\n== 认证头 ==')
for k, v in figma_headers.items():
    log('  %s: %s' % (k, list(v)[:3]))

# 5. 写入 cookie(完整值,供测试使用)
with open(CRED, 'w', encoding='utf-8') as f:
    for k, vs in cookies.items():
        f.write('%s=%s\n' % (k, '|'.join(vs)))
log('\ncookie 名列表: %s' % list(cookies.keys()))
log('creds -> %s' % CRED)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
log('analysis -> %s' % OUT)
