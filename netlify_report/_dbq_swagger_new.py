# -*- coding: utf-8 -*-
"""swagger 新端点实测(只读+无效对象)
migrations 列表(A/B)、ai-gateway token(自己+交叉)、snapshot DELETE 无效id、branch reset 无效id"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token=TOKEN_A, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:700].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== migrations ==')
st, out = api('GET', '/api/v1/sites/%s/database/migrations' % SITE_A)
print('A migrations      [%d] %s' % (st, out[:400]))
st, out = api('GET', '/api/v1/sites/%s/database/migrations?branch=production' % SITE_B, TOKEN_B)
print('B migrations      [%d] %s' % (st, out[:400]))
st, out = api('GET', '/api/v1/sites/%s/database/migrations?branch=agent-6a98d5e6448c07a76d7babf3' % SITE_B, TOKEN_B)
print('B agent migrations[%d] %s' % (st, out[:400]))
print()

print('== ai-gateway token ==')
st, out = api('GET', '/api/v1/sites/%s/ai-gateway/token' % SITE_A)
print('A site token      [%d] %s' % (st, out[:400]))
st, out = api('GET', '/api/v1/accounts/6a979dd2ae93f47d55b62897/ai-gateway/token')
print('A acct token      [%d] %s' % (st, out[:400]))
st, out = api('GET', '/api/v1/sites/%s/ai-gateway/token' % SITE_B)
print('cross B site      [%d] %s' % (st, out[:200]))
print()

print('== snapshot DELETE(无效id)+ branch reset(无效id)==')
st, out = api('DELETE', '/api/v1/sites/%s/database/snapshot/no-such-snap' % SITE_A)
print('snap DEL noid     [%d] %s' % (st, out[:200]))
st, out = api('POST', '/api/v1/sites/%s/database/branch/no-such-branch/reset' % SITE_A, body={'source_branch_id': 'production'})
print('reset noid        [%d] %s' % (st, out[:200]))
st, out = api('POST', '/api/v1/sites/%s/database/branch/production/reset' % SITE_B, TOKEN_A, body={})
print('reset B prod xA   [%d] %s' % (st, out[:200]))
