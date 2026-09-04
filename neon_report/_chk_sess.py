# -*- coding: utf-8 -*-
"""只读验证:生产会话有效性(auth 详情 + 自己项目列表,零写入)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()

def api(path):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json',
         'Cookie': cookie_str()}
    h.update(HEADERS_TEST)
    conn.request('GET', API_BASE + path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

for p in ['/auth', '/projects?limit=5']:
    st, raw = api(p)
    print('== GET %s -> %d' % (p, st))
    try:
        d = json.loads(raw)
        print(json.dumps(d, indent=1, ensure_ascii=False)[:1500])
    except Exception:
        print(raw[:400])
