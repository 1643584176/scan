# -*- coding: utf-8 -*-
"""基线侦察:users/me + organizations + members + invitations + api_keys"""
import json, http.client, ssl, sys

sys.path.insert(0, '.')
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
key = json.load(open('_apikey.json', encoding='utf-8'))['key']

def req(method, path, body=None, tmo=20):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

def show(tag, st, raw, n=1200):
    print('[%s] -> %d' % (tag, st), flush=True)
    print(raw.decode(errors='replace')[:n], flush=True)
    print('', flush=True)

# 1) 当前用户
st, raw = req('GET', '/users/me')
show('users/me', st, raw)

# 2) 我的组织列表
st, raw = req('GET', '/users/me/organizations')
show('users/me/organizations', st, raw)

# 3) 逐个 org 详情 + members + invitations + api_keys
try:
    orgs = json.loads(raw).get('organizations', []) if st == 200 else []
except Exception:
    orgs = []
for o in orgs:
    oid = o.get('id', '')
    print('==== org:', o.get('name'), oid, flush=True)
    st, raw = req('GET', '/organizations/%s' % oid)
    show('org detail', st, raw, 800)
    st, raw = req('GET', '/organizations/%s/members' % oid)
    show('members', st, raw, 1500)
    st, raw = req('GET', '/organizations/%s/invitations' % oid)
    show('invitations', st, raw, 800)
    st, raw = req('GET', '/organizations/%s/api_keys' % oid)
    show('org api_keys', st, raw, 800)
