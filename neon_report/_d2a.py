# -*- coding: utf-8 -*-
"""Data API settings 变异矩阵:db_anon_role 特权化 / openapi_mode / timing / CORS"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'

def req(method, path, body=None, hdrs=None, tmo=20):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    if hdrs: h.update(hdrs)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

def da_get(extra_hdr=None):
    try:
        conn = http.client.HTTPSConnection(DA, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if extra_hdr: h.update(extra_hdr)
        conn.request('GET', '/neondb/rest/v1/', headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status
        stt = dict(r.getheaders()).get('Server-Timing', '') if r.getheaders() else ''
        acao = dict(r.getheaders()).get('Access-Control-Allow-Origin', '') if r.getheaders() else ''
        conn.close()
        return st, raw[:200], stt[:80], acao
    except Exception as e:
        return 0, str(e).encode()[:200], '', ''

def patch_settings(payload, tag):
    st, raw = req('PATCH', '/projects/%s/branches/%s/data-api/neondb' % (P, B), {'settings': payload})
    msg = raw[:200].decode(errors='replace')
    st2, raw2 = req('GET', '/projects/%s/branches/%s/data-api/neondb' % (P, B))
    cur = ''
    try:
        cur = json.dumps(json.loads(raw2).get('settings', {}))[:200]
    except Exception:
        pass
    print('\n[%s] PATCH -> %d | %s' % (tag, st, msg), flush=True)
    print('   now settings:', cur, flush=True)
    return st

print('== baseline anon request ==', flush=True)
print('   ', da_get(), flush=True)

tests = [
    ({'db_anon_role': 'neondb_owner'}, 'anon->neondb_owner'),
    ({'db_anon_role': 'cloud_admin'}, 'anon->cloud_admin'),
    ({'db_anon_role': 'neon_superuser'}, 'anon->neon_superuser'),
    ({'db_anon_role': 'authenticated'}, 'anon->authenticated'),
    ({'openapi_mode': 'ignore-privileges'}, 'openapi ignore-priv'),
    ({'server_timing_enabled': True}, 'server timing'),
    ({'server_cors_allowed_origins': '*'}, 'cors *'),
]
for payload, tag in tests:
    st = patch_settings(payload, tag)
    time.sleep(1.5)
    print('   anon GET /:', da_get(), flush=True)
    # 带 Origin 看 CORS 反射
    if 'cors' in tag:
        print('   with Origin:', da_get({'Origin': 'https://evil.example.com'}), flush=True)

# 还原默认
st = patch_settings({'db_anon_role': 'anonymous', 'openapi_mode': 'disabled', 'server_timing_enabled': False,
                     'server_cors_allowed_origins': None}, 'restore')
time.sleep(1)
print('\nfinal anon:', da_get(), flush=True)
