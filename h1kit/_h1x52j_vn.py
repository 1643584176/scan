# -*- coding: utf-8 -*-
"""h1x52j: VirtualNotification 完整字段 + activity 相关类型(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    try:
        j = r.json()
        print(f'--- {name} [{r.status_code}]')
        if 'errors' in j:
            print(json.dumps(j['errors'])[:300])
        else:
            t = j['data']['__type']
            if t and 'fields' in t:
                for f in t['fields']:
                    print(' ', f['name'], ':', f['type'].get('name') or (f['type'].get('ofType') or {}).get('name'))
            else:
                print(json.dumps(t)[:1500])
    except Exception as e:
        print(f'--- {name} ERR {e}')
    print()

probe('virtual_notif_full', '''query { __type(name: "VirtualNotification") { fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''')
probe('activity_union', '''query { __type(name: "ActivityUnion") { possibleTypes { name } } }''')
