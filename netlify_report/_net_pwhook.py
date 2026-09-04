# -*- coding: utf-8 -*-
"""A: hooks 其它 type(email/slack/github)创建行为
B: site password 保护设置 + 访问绕过矩阵"""
import http.client, ssl, gzip, brotli, json, sys, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25, host='api.netlify.com'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

def probe(tag, m, p, body=None, tok=TOKEN_A, host='api.netlify.com'):
    st, b = req(m, p, body, tok, host=host)
    print('%-60s %s | %s' % (tag, st, b[:220].replace('\n', ' ')))
    return st, b

rnd = ''.join(random.choices(string.ascii_lowercase, k=6))
print('== A. hooks 其它 type ==')
for body in [
    {'type': 'email', 'event': 'deploy_succeeded', 'email': 'zz-%s@qq.com' % rnd},
    {'type': 'email', 'event': 'deploy_failed', 'email': 'zz-%s@example.com' % rnd},
    {'type': 'slack', 'event': 'deploy_succeeded', 'url': 'https://hooks.slack.com/services/T000/B000/%s' % rnd},
    {'type': 'github_app_checks', 'event': 'deploy_succeeded'},
]:
    st, b = probe('POST hook %s' % list(body.items())[:2], 'POST', '/api/v1/hooks?site_id=%s' % SITE_A, body)
    if st in (200, 201):
        try:
            hid = json.loads(b).get('id')
            req('DELETE', '/api/v1/hooks/%s' % hid)
            print('   cleaned', hid)
        except Exception:
            pass
    print()

print()
print('== B1. 设置 site password ==')
st, b = probe('PATCH sites password', 'PATCH', '/api/v1/sites/%s' % SITE_A,
              {'password': 'zz-sec-%s' % rnd})
has_pw = 'has_password' in b and '"has_password":true' in b
print('has_password now:', has_pw)
print()
print('== B2. 访问矩阵 ==')
URLS = [
    ('GET', '/', 'https://sec-test-rcf6lz.netlify.app'),
    ('GET', '/index.html', 'https://sec-test-rcf6lz.netlify.app'),
    ('GET', '/', 'https://6a97c9e3083c963fd210b895--sec-test-rcf6lz.netlify.app'),
    ('GET', '/index.html', 'https://6a97c9e3083c963fd210b895--sec-test-rcf6lz.netlify.app'),
    ('GET', '/', 'http://fuzz-up-9318.com'),
]
for m, p, host in URLS:
    st, b = req(m, p, None, None, host=host.replace('https://', '').replace('http://', ''))
    print('%-22s %-8s %s | %s' % (host, p, st, b[:150].replace('\n', ' ')))
print()
print('== B3. 移除 password 恢复 ==')
st, b = probe('PATCH sites password=null 恢复', 'PATCH', '/api/v1/sites/%s' % SITE_A,
              {'password': ''})
print('done')
