# -*- coding: utf-8 -*-
"""git 代理接口:跨 host + token + header 变体 + Ow 实现"""
import http.client, ssl, gzip, brotli, json, sys, time, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()

def req(host, path, cookie=None, bearer=None, extra=None, method='GET', body=None, timeout=20):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if bearer: h['Authorization'] = 'Bearer ' + bearer
    if extra:
        h.update(extra)
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = body if isinstance(body, bytes) else body.encode()
    t0 = time.time()
    try:
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br': raw = brotli.decompress(raw)
        elif enc == 'gzip': raw = gzip.decompress(raw)
        dt = time.time() - t0
        st = r.status
        body0 = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:200]
        conn.close()
        return st, dt, body0
    except Exception as e:
        return 'ERR', 0, '%s' % e

def show(label, host, path, **kw):
    st, dt, b = req(host, path, **kw)
    print('%-30s %-26s %s %5.1fs | %s' % (label, host + path[:44], st, dt, b))

print('== 各 host 试 git 函数 ==')
show('app A cookie /user', 'app.netlify.com', '/.netlify/functions/git/user', cookie=COOKIE_A)
show('api.netlify.com tokenB /user', 'api.netlify.com', '/.netlify/functions/git/user', bearer=TOKEN_B)
show('api.netlify.com tokenB bare', 'api.netlify.com', '/.netlify/functions/git', bearer=TOKEN_B)
show('app A /repos/..', 'app.netlify.com', '/.netlify/functions/git/repos/1643584176/scan', cookie=COOKIE_A)
show('app A POST user', 'app.netlify.com', '/.netlify/functions/git/user', cookie=COOKIE_A, method='POST', body=b'{}')
show('app B cookie /user', 'app.netlify.com', '/.netlify/functions/git/user', cookie=COOKIE_B)

print()
print('== app.netlify.com 已知函数对照 ==')
show('dbq exists', 'app.netlify.com', '/.netlify/functions/database-query', cookie=COOKIE_A, method='POST', body=json.dumps({'siteId': '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', 'action': 'check', 'sql': 'select 1'}))
show('verify exists', 'app.netlify.com', '/.netlify/functions/verify?domain=example.com', cookie=COOKIE_A)
show('nonexistent fn', 'app.netlify.com', '/.netlify/functions/no-such-fn-xyz', cookie=COOKIE_A)

print()
print('== git client 实现(Ow / root 用法)==')
for fn in [r'D:\scan\netlify_report\_js\net_actions.js', r'D:\scan\netlify_report\_js\net_lib.js', r'D:\scan\netlify_report\_js\net_helpers.js']:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    for key in ['api.github.com', 'root:"/.netlify/functions/git', 'github.com/api', 'graphql']:
        for m in list(re.finditer(re.escape(key), data))[:2]:
            s = max(0, m.start() - 350)
            e = min(len(data), m.end() + 350)
            print('=====', fn.split('\\')[-1], '|', key)
            print(data[s:e].replace('\n', ' ')[:700])
