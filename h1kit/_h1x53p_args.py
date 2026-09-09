# -*- coding: utf-8 -*-
"""h1x53p: 查目标字段参数必填性 + ExternalIntegrationProvider 枚举值 + DerivedPentest origin_type 提示"""
import json, sys, io, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def gql(q):
    req = urllib.request.Request('https://hackerone.com/graphql',
        data=json.dumps({'query': q}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__err': str(e)}

q = """
query {
  __type(name: "Query") {
    fields {
      name
      args { name type { kind name ofType { kind name ofType { name } } } defaultValue }
    }
  }
}
"""
r = gql(q)
if 'data' in r:
    want = ['automation', 'webhook', 'external_integration_credentials', 'pentest_report',
            'derived_pentest', 'hai_chat', 'hai_task', 'pentest_opportunity']
    for f in r['data']['__type']['fields']:
        if f['name'] in want:
            args = []
            for a in (f.get('args') or []):
                t = a['type']
                nm = t.get('name') or (t.get('ofType') or {}).get('name') or (((t.get('ofType') or {}).get('ofType') or {}).get('name'))
                nonnull = t['kind'] == 'NON_NULL' or ((t.get('ofType') or {}).get('kind') == 'NON_NULL')
                args.append(f"{a['name']}:{nm}{'!' if nonnull else ''}")
            print(f"{f['name']}({', '.join(args)})")
else:
    print('失败:', str(r)[:300])

for tname in ['ExternalIntegrationProvider', 'HaiTaskStateEnum', 'PentestReportTypeEnum']:
    r2 = gql(f'query{{ __type(name: "{tname}") {{ kind enumValues {{ name }} }} }}')
    if r2.get('data', {}).get('__type'):
        ev = r2['data']['__type'].get('enumValues')
        print(f'{tname}:', [e['name'] for e in ev] if ev else '(no enumValues)')
    else:
        print(f'{tname}: not found')
