# -*- coding: utf-8 -*-
"""Netlify:验证 NETLIFY_FUNCTIONS_TOKEN(来自函数 env)对平台 API 的权限 + 新账户凭证保存"""
import http.client, ssl, gzip, brotli, sys, json, time
sys.path.insert(0, r'D:\scan\netlify_report')

# probe2 返回的凭证(账户 169879185114)
AWS = {
    'access_key': 'ASIASPDMWU3NCIXPN4GU',
    'secret_key': 'jW14CINxjNDeqxJOPn6t2fzur0YIqjoNwng/ZrVq',
    'session_token': None,  # 在 _aws_creds2.json 读取
    'account': '169879185114'
}
NF_TOKEN = '062d3d30-a9b9-4477-aa69-4a3dba0d5b30'

ctx = ssl.create_default_context()

def api(host, path, token, method='GET', body=None, ctype='application/json'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token, 'Content-Type': ctype}
    payload = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

print('=== NETLIFY_FUNCTIONS_TOKEN 平台 API 探测 ===')
for path in ['/api/v1/user', '/api/v1/sites?per_page=3', '/api/v1/accounts', '/api/v1/account']:
    try:
        st, raw = api('api.netlify.com', path, NF_TOKEN)
        print('GET %s -> %d %s' % (path, st, raw[:400].decode('utf-8', 'replace').replace('\n', ' ')))
    except Exception as e:
        print('GET %s ERR %s' % (path, str(e)[:100]))

print()
print('=== 对照:账号A token ===')
for path in ['/api/v1/user']:
    try:
        st, raw = api('api.netlify.com', path, sys.modules['_net_creds'].TOKEN_A)
        print('GET %s -> %d %s' % (path, st, raw[:300].decode('utf-8', 'replace').replace('\n', ' ')))
    except Exception as e:
        print('GET %s ERR %s' % (path, str(e)[:100]))
