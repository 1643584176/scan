# -*- coding: utf-8 -*-
"""h1x53u: 补扫 Report 类型全字段(敏感名)+ ActivityUnion 成员确认"""
import json, sys, io, urllib.request, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def gql(q):
    req = urllib.request.Request('https://hackerone.com/graphql',
        data=json.dumps({'query': q}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__err': str(e)}

KEYS = re.compile(r'(original|duplicate|dup|related|source|reference|origin|link|merged|merge|supersed|parent|child|cross|collab|clone|import)', re.I)

# 1. Report 全字段
q = 'query{ __type(name: "Report") { fields { name type { kind name ofType { kind name ofType { name } } } } } }'
r = gql(q)
print('=== Report 全字段数 ===')
flds = {}
if r.get('data', {}).get('__type', {}).get('fields'):
    for f in r['data']['__type']['fields']:
        t = f['type']
        nm = t.get('name') or (t.get('ofType') or {}).get('name') or (((t.get('ofType') or {}).get('ofType') or {}).get('name'))
        flds[f['name']] = nm
    print('total:', len(flds))
    hits = [(f, t) for f, t in flds.items() if KEYS.search(f) or KEYS.search(t or '')]
    print('--- 敏感字段:')
    for f, t in hits:
        print(f'   {f}: {t}')
    print('--- 全部字段(按名字含 report/activity 连接类):')
    for f, t in sorted(flds.items()):
        if any(k in f.lower() for k in ['report', 'activity', 'duplicate', 'original', 'source', 'reference', 'cloned']):
            print(f'   {f}: {t}')
else:
    print('Report introspection 失败:', str(r)[:300])

# 2. Report.activities 连接的类型链
for qn in ['report(id: 3992341){ activities { edges { node { __typename } } } }'.replace(' 3992341', ' 1'),
           '']:
    pass
# 用 introspection 找 activities 字段返回的连接类型
q2 = 'query{ __type(name: "ReportActivityConnection") { fields { name } } }'
r2 = gql(q2)
print('\nReportActivityConnection:', json.dumps(r2.get('data'), ensure_ascii=False)[:300])
