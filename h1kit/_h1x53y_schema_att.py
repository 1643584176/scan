# -*- coding: utf-8 -*-
import json, sys, io, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
def gql(q):
    req = urllib.request.Request('https://hackerone.com/graphql',
        data=json.dumps({'query': q}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__err': str(e)}
r = gql('query{ __schema { types { name kind } } }')
ts = r.get('data', {}).get('__schema', {}).get('types', [])
print('total types:', len(ts))
for t in ts:
    n = t.get('name', '')
    if any(k in n.lower() for k in ['attach', 'file', 'image', 'media', 'download']):
        print(t.get('kind'), n)
