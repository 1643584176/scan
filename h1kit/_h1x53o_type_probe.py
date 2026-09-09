# -*- coding: utf-8 -*-
"""h1x53o: __type introspection - automation/webhook/pentest_report/clusters/derived_pentest/rom_asset_group/hai_task/hai_chat/pentest 返回类型与关键字段"""
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

# 1. 查根字段的返回类型(通过 __schema? 禁。用 __type(Query) 拿字段返回类型)
q = """
query {
  __type(name: "Query") {
    fields {
      name
      type { kind name ofType { kind name ofType { kind name ofType { name } } } }
    }
  }
}
"""
r = gql(q)
fields = {}
if 'data' in r:
    for f in r['data']['__type']['fields']:
        t = f['type']
        nm = t.get('name') or (t.get('ofType') or {}).get('name') or (((t.get('ofType') or {}).get('ofType') or {}).get('name'))
        fields[f['name']] = nm
else:
    print('Query __type 失败:', str(r)[:300])

want = ['automation', 'webhook', 'pentest_report', 'pentest', 'clusters', 'derived_pentest',
        'rom_asset_group', 'hai_task', 'hai_chat', 'external_integration_credentials',
        'tray_solution_instance_url', 'embedded_submission_form', 'custom_dashboard']
for w in want:
    print(f'{w} -> {fields.get(w)}')

# 2. 逐个 introspection 返回类型字段
for w in want:
    tn = fields.get(w)
    if not tn or tn == 'Query':
        continue
    q2 = f"""
query {{
  __type(name: "{tn}") {{
    kind
    fields {{
      name
      type {{ kind name ofType {{ kind name ofType {{ kind name }}}}}} 
    }}
  }}
}}
"""
    r2 = gql(q2)
    if 'data' in r2 and r2['data']['__type']:
        fl = r2['data']['__type']['fields'] or []
        out = []
        for f in fl[:60]:
            t = f['type']
            nm = t.get('name') or (t.get('ofType') or {}).get('name') or (((t.get('ofType') or {}).get('ofType') or {}).get('name'))
            out.append(f"{f['name']}:{nm}")
        print(f'== {tn} ({len(fl)} fields) ==')
        print(' '.join(out))
    else:
        print(f'== {tn} introspection 失败:', str(r2)[:200])
