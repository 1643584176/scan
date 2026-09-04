# -*- coding: utf-8 -*-
"""越权对测准备:探查账号 B 的 site 列表 + database 功能状态
1. GET /api/v1/sites(账号 B token)
2. 对每个 site 试 GET /api/v1/sites/{id}/database
"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B, COOKIE_B

ctx = ssl.create_default_context()


def api(method, path, cookie=None, token=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    if token:
        h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    body = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, body


# 1. B 的 sites
st, b = api('GET', '/api/v1/sites?per_page=100', token=TOKEN_B)
print('B_sites          [%d]' % st)
try:
    sites = json.loads(b)
    for s in sites:
        print('   id=%s name=%s url=%s' % (s.get('id'), s.get('name'), s.get('ssl_url')))
except Exception as e:
    print('   parse fail:', b[:800], e)
print()

# 2. B 每个 site 的 database 状态
try:
    for s in sites:
        sid = s.get('id')
        st2, b2 = api('GET', '/api/v1/sites/%s/database' % sid, token=TOKEN_B)
        print('B_db_%s          [%d] %s' % (s.get('name'), st2, b2[:600]))
except NameError:
    print('no sites parsed')
