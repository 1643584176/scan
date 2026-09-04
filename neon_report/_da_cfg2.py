# -*- coding: utf-8 -*-
"""GET data-api 当前配置 + PATCH 触发刷新后立即测新 key"""
import json, http.client, ssl, sys, time

sys.path.insert(0, '.')
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
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

# 1) GET 当前 data-api 状态
st, raw = req('GET', '/projects/%s/branches/%s/data-api/neondb' % (P, B))
print('GET data-api:', st)
print(raw.decode(errors='replace')[:1500], flush=True)

if st == 200:
    cfg = json.loads(raw)
    settings = cfg.get('settings', {})
    print('\ncurrent settings:', json.dumps(settings, ensure_ascii=False), flush=True)
    # 2) PATCH 保真(同值回写,触发 schema cache 刷新)
    body = {'settings': settings}
    st2, raw2 = req('PATCH', '/projects/%s/branches/%s/data-api/neondb' % (P, B), body)
    print('PATCH refresh:', st2, raw2.decode(errors='replace')[:300], flush=True)
