# -*- coding: utf-8 -*-
"""git 代理收尾:403 来源头 + 写方法白名单 + 清理私有 repo"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='GET', body=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
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
    hd = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    return r.status, dt, hd, raw.decode('utf-8', 'ignore').replace('\n', ' ')[:220]

def show(label, path, method='GET', body=None):
    st, dt, hd, b = req(path, method=method, body=body)
    rl = hd.get('x-ratelimit-remaining', hd.get('x-ratelimit-limit', '?'))
    print('%-34s %s %5.1fs rl=%s | %s' % (label, st, dt, rl, b))

print('== 403 来源:代理 vs 直连 GitHub 头对比 ==')
show('proxy netlify/cli', '/.netlify/functions/git/repos/netlify/cli')
show('proxy scan(对照)', '/.netlify/functions/git/repos/1643584176/scan')

print()
print('== 写方法白名单(repos 前缀内)==')
show('PATCH scan {}', '/.netlify/functions/git/repos/1643584176/scan', method='PATCH', body=b'{}')
show('POST issues', '/.netlify/functions/git/repos/1643584176/scan/issues', method='POST', body=b'{"title":"x"}')
show('PUT contents(假路径)', '/.netlify/functions/git/repos/1643584176/scan/contents/zz-not-exist.txt', method='PUT',
     body=json.dumps({'message': 't', 'content': 'eA=='}).encode())
show('DELETE 假分支 ref', '/.netlify/functions/git/repos/1643584176/scan/git/refs/heads/zz-no-branch', method='DELETE')
print('done')
