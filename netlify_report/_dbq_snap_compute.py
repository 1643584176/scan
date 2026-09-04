# -*- coding: utf-8 -*-
"""快照 + compute 校验探测
1. B 的 snapshots 列表(B token)
2. snapshot restore 交叉(A token + B snapshotId + A site?)——用不存在 id 先测校验
3. compute/settings 非法值(类型错,无副作用)
"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + token}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== B snapshots ==')
st, out = api('GET', '/api/v1/sites/%s/database/snapshots' % SITE_B, TOKEN_B)
print('[%d] %s' % (st, out[:800]))
print()

print('== snapshot restore 校验(不存在 id + 交叉) ==')
st, out = api('POST', '/api/v1/sites/%s/database/snapshot/no-such-snap/restore' % SITE_A, TOKEN_A,
              {'branch_name': 'x'})
print('A_site+noid      [%d] %s' % (st, out[:200]))
st, out = api('POST', '/api/v1/sites/%s/database/snapshot/no-such-snap/restore' % SITE_B, TOKEN_A,
              {'branch_name': 'x'})
print('A-tok+B_site     [%d] %s' % (st, out[:200]))
print()

print('== compute/settings 非法值(类型错/负数,无实际配置) ==')
st, out = api('GET', '/api/v1/sites/%s/database/compute/settings' % SITE_A, TOKEN_A)
print('GET compute      [%d] %s' % (st, out[:300]))
for bad in [{'min_cu': 'abc'}, {'sleep_timeout_seconds': 'abc'}, {'min_cu': -1}, {'max_cu': 0.0001}]:
    st, out = api('PUT', '/api/v1/sites/%s/database/compute/settings' % SITE_A, TOKEN_A, bad)
    print('PUT %-28s [%d] %s' % (str(bad), st, out[:200]))
