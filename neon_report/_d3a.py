# -*- coding: utf-8 -*-
"""Neon Auth 集成:create 三 provider 值全试,看响应/密钥形态"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
ORG = 'org-flat-dawn-91601224'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, tmo=25):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

# 现状
st, raw = req('GET', '/projects/%s/auth/integrations' % P)
print('integrations now -> %d | %s' % (st, raw[:300].decode(errors='replace')), flush=True)

for prov in ['better_auth', 'stack', 'mock']:
    body = {'auth_provider': prov, 'project_id': P, 'branch_id': B,
            'database_name': 'neondb', 'role_name': 'neondb_owner'}
    st, raw = req('POST', '/projects/auth/create', body)
    msg = raw[:700].decode(errors='replace')
    print('\n[create %s] -> %d' % (prov, st), flush=True)
    print('  ', msg, flush=True)
    if st == 200 or st == 201:
        open(r'D:\scan\neon_report\_auth_%s.json' % prov, 'w').write(raw.decode(errors='replace'))
        try:
            d = json.loads(raw)
            # 敏感字段单独摘要(不打印全文)
            for k in ['secret_server_key', 'pub_client_key', 'jwks_url', 'base_url', 'auth_provider_project_id', 'schema_name', 'table_name']:
                v = d.get(k) or (d.get('integration') or {}).get(k)
                if v:
                    print('   %s = %s' % (k, (str(v)[:40] + '...' if len(str(v)) > 40 else v)), flush=True)
        except Exception:
            pass
    time.sleep(1.5)
