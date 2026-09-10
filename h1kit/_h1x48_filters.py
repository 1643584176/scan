# -*- coding: utf-8 -*-
"""h1x48: Filter 类型全字段(SQL 注入面侦查)
FiltersReportFilterInput 等 where 谓词 + StringPredicate 类型"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

def intro(tname):
    q = f'{{ __type(name: "{tname}") {{ inputFields {{ name type {{ kind name ofType {{ kind name ofType {{ kind name }} }} }} }} }} }}'
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    try:
        return r.json()['data']['__type']
    except Exception:
        return None

for t in ['FiltersReportFilterInput', 'StringPredicateInput', 'IntPredicateInput', 'DatetimePredicateInput', 'FiltersTeamFilterInput']:
    f = intro(t)
    print(f'===== {t} =====')
    if not f:
        print('  (null)')
        continue
    for x in f.get('inputFields') or []:
        tp = x['type']
        tn = tp['name'] or (tp.get('ofType') or {}).get('name') or ((tp.get('ofType') or {}).get('ofType') or {}).get('name') or '?'
        print(f'  {x["name"]} : {tn}')
    print()
