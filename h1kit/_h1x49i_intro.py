# -*- coding: utf-8 -*-
"""introspect HacktivityDocument + DocumentUnion 成员"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

for tname in ['HacktivityDocument', 'DocumentUnion']:
    q = '{ __type(name: "%s") { kind fields { name type { kind name ofType { kind name } } } possibleTypes { name } } }' % tname
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    j = r.json().get('data', {}).get('__type')
    print('=====', tname, '=====')
    if not j:
        print(r.text[:200]); continue
    print('kind:', j.get('kind'))
    for f in (j.get('fields') or []):
        t = f['type']
        nm = t.get('name') or ''
        if not nm and t.get('ofType'):
            nm = t['ofType'].get('name') or ''
        print('  %s -> %s' % (f['name'], nm))
    for p in (j.get('possibleTypes') or []):
        print('  possibleType:', p['name'])
