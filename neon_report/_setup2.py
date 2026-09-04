# -*- coding: utf-8 -*-
"""setup2:项目已建 -> 分支/DataAPI/Bucket/Credential 建立(org_id 内嵌 body 模式)"""
import http.client, ssl, json, sys, time
ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

def show(tag, st, raw, cut=700):
    print('\n== %s -> %d' % (tag, st))
    try:
        print(json.dumps(json.loads(raw), indent=1, ensure_ascii=False)[:cut])
    except Exception:
        print(raw[:250])

# 列出刚建的项目(名字 sec-apikey-1 / sec-q / sec-i 系列,取最新)
st, raw = req('GET', '/projects?org_id=%s' % ORG)
d = json.loads(raw)
projs = d.get('projects', [])
print('total projects:', len(projs))
for p in projs:
    print('  -', p.get('id'), p.get('name'), p.get('org_id'), p.get('created_at'))
pid = None
for p in projs:
    if p.get('name', '').startswith('sec-'):
        pid = p['id']
        break
if not pid and projs:
    pid = projs[-1]['id']
print('use pid:', pid)

# 分支
st, raw = req('GET', '/projects/%s/branches' % pid)
show('GET branches', st, raw, 900)
branches = json.loads(raw).get('branches', [])
bid = branches[0]['id'] if branches else None
print('bid:', bid)

ctxj = {'pid': pid, 'bid': bid, 'org': ORG}
open(r'D:\scan\neon_report\_ctx.json', 'w').write(json.dumps(ctxj))
time.sleep(1)

if bid:
    # Data API
    st, raw = req('POST', '/projects/%s/branches/%s/data-api/neondb' % (pid, bid), {})
    show('POST data-api', st, raw, 400)
    time.sleep(2)
    # Bucket
    st, raw = req('POST', '/projects/%s/branches/%s/buckets' % (pid, bid), {'name': 't1', 'access_level': 'private'})
    show('POST bucket', st, raw, 400)
    time.sleep(1)
    # Credential
    st, raw = req('POST', '/projects/%s/branches/%s/credentials' % (pid, bid),
                  {'name': 'cred1', 'scopes': ['storage:read', 'functions:invoke', 'ai_gateway:invoke'], 'principal_type': 'user'})
    show('POST credential', st, raw, 600)
