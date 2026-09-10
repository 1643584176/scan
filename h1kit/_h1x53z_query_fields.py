# -*- coding: utf-8 -*-
"""h1x53z: Query 根字段全清单 + 参数(对照已测清单找漏网)"""
import json, sys, io, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def gql(q):
    req = urllib.request.Request('https://hackerone.com/graphql',
        data=json.dumps({'query': q}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__err': str(e)}

q = ('query{ __type(name: "Query") { fields { name '
     'args { name type { kind name ofType { kind name ofType { name } } } defaultValue } '
     'type { kind name ofType { kind name ofType { name } } } } } }')
r = gql(q)
flds = r.get('data', {}).get('__type', {}).get('fields')
if not flds:
    print('ERR', str(r)[:300])
    sys.exit()
print('TOTAL Query fields:', len(flds))
for f in sorted(flds, key=lambda x: x['name']):
    t = f['type']
    tn = t.get('name') or (t.get('ofType') or {}).get('name') or (((t.get('ofType') or {}).get('ofType') or {}).get('name'))
    args = []
    for a in f.get('args', []):
        at = a['type']
        an = at.get('name') or (at.get('ofType') or {}).get('name') or (((at.get('ofType') or {}).get('ofType') or {}).get('name'))
        args.append('%s:%s' % (a['name'], an))
    print('%s -> %s | args: %s' % (f['name'], tn, ', '.join(args)))
