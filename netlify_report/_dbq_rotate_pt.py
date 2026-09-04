# -*- coding: utf-8 -*-
"""② rotate 通道透传探测(安全变体:Neon 格式不存在的 id,零副作用)
若返回 "branch not found"(Netlify 层校验) -> 不透传,闭合
若返回 Neon 层错误/其他形态 -> 透传证据,再决定
"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()


def api(method, path, token, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


cases = [
    ('rotate br-no-such-neon-xxx', '/api/v1/sites/%s/database/rotate_credentials' % SITE_A,
     {'rotations': [{'branch': 'br-no-such-neon-xxx', 'roles': ['netlifydb_owner']}]}),
]
# 注:第二 case(真实 B 的 br-xxx)仅当第一 case 显示透传迹象时才启用
# ('rotate br-holy-bar-aekgctv2(B真实Neonid)', ...)
for name, path, body in cases:
    st, out = api('POST', path, TOKEN_A, body)
    print('%-42s [%d] %s' % (name, st, out[:300]))
