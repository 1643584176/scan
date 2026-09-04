# -*- coding: utf-8 -*-
"""verify 第3/4节 + git 探测(接上次中断)"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='GET', body=None, timeout=30):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = body if isinstance(body, bytes) else body.encode()
    t0 = time.time()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    conn.close()
    return st, raw.decode('utf-8', 'ignore').replace('\n', ' ')[:300], dt

def show(label, path, ck=COOKIE_A, method='GET', body=None):
    st, raw, dt = req(path, ck, method=method, body=body)
    print('%-28s %s %6.1fs | %s' % (label, st, dt, raw))
    return st, raw, dt

print('==== 3. domain 参数结构变异 ====')
show('GET ?domain=a&domain=b', '/.netlify/functions/verify?domain=aaa.com&domain=bbb.com')
show('POST {"domain"}', '/.netlify/functions/verify', method='POST', body=json.dumps({'domain': 'example.com'}))
show('POST {"domains":[]}', '/.netlify/functions/verify', method='POST', body=json.dumps({'domains': ['example.com']}))
show('no param', '/.netlify/functions/verify')
show('other param', '/.netlify/functions/verify?site=example.com')

print()
print('==== 4. git 接口形态 ====')
show('git bare GET', '/.netlify/functions/git')
show('git /repos GET', '/.netlify/functions/git/repos')
show('git /user GET', '/.netlify/functions/git/user')
show('git POST {}', '/.netlify/functions/git', method='POST', body=b'{}')
show('git ?path=', '/.netlify/functions/git?path=repos')
show('git search', '/.netlify/functions/git/search/repositories?q=netlify')
print('done')
