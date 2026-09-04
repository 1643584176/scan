# -*- coding: utf-8 -*-
"""url hook 创建: url 校验边界矩阵"""
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

def probe(tag, url):
    st, b = req('POST', '/api/v1/hooks?site_id=%s' % SITE_A,
                {'type': 'url', 'event': 'deploy_succeeded', 'url': url})
    ok = st in (200, 201)
    print('%-22s %s %s | %s' % ('OK ' if ok else 'FAIL', url[:60], st, b[:180].replace('\n', ' ')))
    if ok:
        try:
            hid = json.loads(b).get('id')
            req('DELETE', '/api/v1/hooks/%s' % hid)
            print('   -> cleaned', hid)
        except Exception:
            pass
    return ok

rnd = ''.join(random.choices(string.ascii_lowercase, k=6))
urls = [
    # 基础公网
    'https://example.com', 'https://example.com/', 'https://www.example.com/path',
    'https://example.com/path?q=1', 'https://example.com:8443/x',
    'http://example.com/x', 'example.com/x', '//example.com/x',
    # 特殊字符
    'https://example.com/%s' % rnd, 'https://example.com/a b',
    # IP 与保留段
    'https://1.1.1.1/x', 'http://1.1.1.1/x', 'https://127.0.0.1/x',
    'http://127.0.0.1:8000/x', 'http://169.254.169.254/latest/meta-data/',
    'http://0.0.0.0/x', 'http://[::1]:80/x', 'http://10.0.0.1/x',
    'http://192.168.1.1/x', 'http://172.16.0.1/x', 'http://2130706433/x',
    # 域名字面 vs 解析
    'http://localhost/x', 'http://metadata.google.internal/x',
    'http://spoofed.burpcollaborator.net/x',
    # 协议变形
    'ftp://example.com/x', 'file:///etc/passwd', 'gopher://example.com:70/x',
    'https://user:pass@example.com/x', 'https://example.com@127.0.0.1/x',
    'https://127.0.0.1@example.com/x',
    # url 编码/换行
    'https://example.com/x%0d%0aX-Injected:1', 'https://example.com/%2e%2e/x',
]
for u in urls:
    probe(rnd, u)
print('done')
