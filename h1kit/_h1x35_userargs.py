# -*- coding: utf-8 -*-
"""h1x35: users/hackerone_triagers 参数 introspection + analytics 登录态线索确认"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# 匿名 introspection 拿参数结构(不需要登录,__type 开放)
qs = {
    'users_args': '{ __type(name: "Query") { fields { name args { name type { kind name ofType { name } } } } } }',
}
r = s.post('https://hackerone.com/graphql', json={'query': qs['users_args']}, timeout=30)
import json
j = r.json()
flds = {}
for f in j.get('data', {}).get('__type', {}).get('fields', []):
    if f['name'] in ('users', 'hackerone_triagers', 'analytics_reports', 'analytics_chart', 'teams', 'me', 'current_user'):
        flds[f['name']] = [a['name'] for a in f['args']]
print('roots args:', json.dumps(flds, indent=1))
for t in ['FiltersUserFilterInput', 'UserSearchInput']:
    rr = s.post('https://hackerone.com/graphql', json={'query': f'{{ __type(name: "{t}") {{ inputFields {{ name type {{ kind name ofType {{ kind name }} }} }} }} }}'}, timeout=30)
    print(t, rr.text[:800])
