# -*- coding: utf-8 -*-
"""Functions 写操作矩阵(带 CSRF):
1. PATCH/DELETE bogus slug(404 形态)
2. POST deployments:json 错误形态 -> multipart 空 -> 不存在 slug 的部署行为(隐式创建?)
3. list 复查"""
import http.client, ssl, json, re, html, os, sys, random, string

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def ctl_req(method, path, body=None, ctype='application/json', raw_body=None):
    # 1. GET / 刷新 csrf
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    body0 = r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    txt = body0.decode('utf-8', 'replace')
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if ctype:
        hdrs['Content-Type'] = ctype
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path, body=data, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

slug = 'zz' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
FP = '/projects/%s/branches/%s/functions' % (PID, BID)

print('=== [1] PATCH/DELETE bogus slug(带 CSRF) ===', flush=True)
st, raw = ctl_req('PATCH', API_BASE + FP + '/' + slug, {'name': 'x'})
print('PATCH -> %d %s' % (st, raw[:250].replace('\n', ' ')), flush=True)
st, raw = ctl_req('DELETE', API_BASE + FP + '/' + slug)
print('DELETE -> %d %s' % (st, raw[:250].replace('\n', ' ')), flush=True)

print('\n=== [2] deployments 错误形态 ===', flush=True)
st, raw = ctl_req('POST', API_BASE + FP + '/' + slug + '/deployments', {})
print('json {} -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)
st, raw = ctl_req('POST', API_BASE + FP + '/' + slug + '/deployments', None, ctype='multipart/form-data; boundary=xxb',
                  raw_body=b'--xxb\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n--xxb--\r\n')
print('multipart runtime only -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== [3] PATCH name 校验(无 slug 时) ===', flush=True)
for nm in ['', '   ', 'a' * 300, 'ok-name-123', 'x' * 256]:
    st, raw = ctl_req('PATCH', API_BASE + FP + '/' + slug, {'name': nm})
    print('name=%r -> %d %s' % (nm[:20], st, raw[:220].replace('\n', ' ')), flush=True)

print('\n=== [4] slug 校验形态(特殊字符) ===', flush=True)
for s2 in ['UPPER-SLUG', 'with_underscore', 'a..b', '-lead', 'trail-', 'x' * 100]:
    st, raw = ctl_req('GET', API_BASE + FP + '/' + s2)
    print('GET %s -> %d %s' % (s2, st, raw[:180].replace('\n', ' ')), flush=True)
