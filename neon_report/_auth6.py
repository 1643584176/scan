# -*- coding: utf-8 -*-
"""skip_role_creation 特权角色组合(短名重试)"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, tmo=15):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

vecs = [
    ('skipc', {'role_names': ['cloud_admin'], 'skip_role_creation': True}),
    ('skipn', {'role_names': ['neon_superuser'], 'skip_role_creation': True}),
    ('skipo', {'role_names': ['neondb_owner'], 'skip_role_creation': True}),
    ('noskipo', {'role_names': ['neondb_owner'], 'skip_role_creation': False}),
]
for name, extra in vecs:
    body = {'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs', 'provider_name': 'p%s' % name}
    body.update(extra)
    st, raw = req('POST', '/projects/%s/jwks' % P, body)
    msg = raw[:260].decode(errors='replace')
    print('[%s] -> %d | %s' % (name, st, msg), flush=True)
    time.sleep(1.2)

# 清理本次创建的所有 p* provider
st, raw = req('GET', '/projects/%s/jwks' % P)
for j in json.loads(raw).get('jwks', []):
    nm = j.get('provider_name', '')
    if nm.startswith('p'):
        st2, raw2 = req('DELETE', '/projects/%s/jwks/%s' % (P, j['id']))
        print('cleanup %s -> %d' % (nm, st2), flush=True)
