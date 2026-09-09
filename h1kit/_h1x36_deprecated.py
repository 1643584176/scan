# -*- coding: utf-8 -*-
"""h1x36: 拉取所有类型的 deprecated 字段(老字段=老权限逻辑高发区)
Query/Report 全量 includeDeprecated"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

def intro(tname):
    q = f'{{ __type(name: "{tname}") {{ name fields(includeDeprecated: true) {{ name isDeprecated deprecationReason args {{ name }} }} }} }}'
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
    try:
        j = r.json()
        f = j['data']['__type']
        if not f:
            return []
        out = []
        for x in f.get('fields') or []:
            if x.get('isDeprecated'):
                out.append(x)
        return out
    except Exception:
        return []

for tname in ['Query', 'Report']:
    dep = intro(tname)
    print(f'===== {tname} deprecated fields: {len(dep)} =====')
    for d in dep:
        print(' -', d['name'], '|', (d.get('deprecationReason') or '')[:100], '| args:', [a['name'] for a in d.get('args') or []])
    print()
