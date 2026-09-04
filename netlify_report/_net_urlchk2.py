# -*- coding: utf-8 -*-
"""url hook: 真实域名 + 域名解析边界(校验器行为建模)"""
import http.client, ssl, gzip, brotli, json, sys, socket, random, string
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

def probe(tag, url):
    st, b = req('POST', '/api/v1/hooks?site_id=%s' % SITE_A,
                {'type': 'url', 'event': 'deploy_succeeded', 'url': url})
    ok = st in (200, 201)
    print('%-5s %-52s %s | %s' % ('OK' if ok else 'FAIL', url[:50], st, b[:150].replace('\n', ' ')))
    if ok:
        try:
            hid = json.loads(b).get('id')
            req('DELETE', '/api/v1/hooks/%s' % hid)
            print('   cleaned', hid)
        except Exception:
            pass

urls = [
    # 真实知名域
    'https://www.google.com/', 'https://www.qq.com/', 'https://www.netlify.com/',
    'https://api.netlify.com/', 'https://www.baidu.com/',
    # 我们可控的 netlify URL(不存在的子域也测)
    'https://6a97c9e3083c963fd210b895--sec-test-rcf6lz.netlify.app/',
    'https://zz-nonexist-12345.netlify.app/', 'https://netlify.app/',
    # 其它 TLD
    'https://www.github.com/', 'https://www.microsoft.com/',
]
for u in urls:
    probe('', u)

print()
print('== 域名解析对照(本地) ==')
for u in ['www.example.com', 'www.google.com', '6a97c9e3083c963fd210b895--sec-test-rcf6lz.netlify.app']:
    try:
        print(u, '->', socket.gethostbyname(u))
    except Exception as e:
        print(u, 'ERR', e)
print('done')
