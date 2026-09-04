# -*- coding: utf-8 -*-
"""重测 snapshot restore 交叉鉴权(不存在 id,无副作用)"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    try:
        out = raw.decode('utf-8', 'ignore')
    except Exception:
        out = repr(raw[:200])
    st = r.status
    conn.close()
    return st, out


cases = [
    ('A_tok+B_site+nosnap', '/api/v1/sites/%s/database/snapshot/no-such-snap-xyz/restore' % SITE_B, TOKEN_A),
    ('B_tok+A_site+nosnap', '/api/v1/sites/%s/database/snapshot/no-such-snap-xyz/restore' % SITE_A, TOKEN_B),
    ('A_tok+A_site+nosnap', '/api/v1/sites/%s/database/snapshot/no-such-snap-xyz/restore' % SITE_A, TOKEN_A),
    ('B_tok+B_site+nosnap', '/api/v1/sites/%s/database/snapshot/no-such-snap-xyz/restore' % SITE_B, TOKEN_B),
    ('A_tok+B_site+real_snap_but_A_branch_name', '/api/v1/sites/%s/database/snapshot/snap-holy-queen-aes1v64g/restore' % SITE_B, TOKEN_A),
]
for name, path, tok in cases:
    st, out = api('POST', path, tok, {'branch_name': 'zz-no-such-branch-xyz'})
    print('%-42s [%d] %s' % (name, st, out[:250]))
    print()
