# -*- coding: utf-8 -*-
"""hooks POST 字段嵌套形态测试(email/slack/url)"""
import http.client, ssl, gzip, brotli, json, sys, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
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

rnd = ''.join(random.choices(string.ascii_lowercase, k=6))
bodies = [
    # 嵌套 fields
    {'type': 'email', 'event': 'deploy_succeeded', 'fields': {'email': 'zz-%s@qq.com' % rnd}},
    # 顶层 + data
    {'type': 'email', 'event': 'deploy_succeeded', 'data': {'email': 'zz-%s@qq.com' % rnd}},
    # subject 模板
    {'type': 'email', 'event': 'deploy_failed', 'email': 'zz-%s@qq.com' % rnd,
     'subject_template': 'zz'},
    # slack 嵌套
    {'type': 'slack', 'event': 'deploy_succeeded',
     'fields': {'url': 'https://hooks.slack.com/services/T/B/%s' % rnd, 'channel': '#zz'}},
]
for body in bodies:
    st, b = req('POST', '/api/v1/hooks?site_id=%s' % SITE_A, body)
    print('%-12s %s | %s' % (list(body.keys()), st, b[:260].replace('\n', ' ')))
    if st in (200, 201):
        try:
            hid = json.loads(b).get('id')
            req('DELETE', '/api/v1/hooks/%s' % hid)
            print('   cleaned', hid)
        except Exception:
            pass
    print()
print('done')
