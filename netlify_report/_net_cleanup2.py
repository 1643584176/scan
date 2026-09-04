# -*- coding: utf-8 -*-
"""收尾清理: SITE_A custom_domain fuzz-up-9318.com(配额窗口可能已过) + 残留检查"""
import http.client, ssl, gzip, brotli, json, sys
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

def probe(tag, m, p, body=None):
    st, b = req(m, p, body)
    print('%-50s %s | %s' % (tag, st, b[:220].replace('\n', ' ')))
    return st, b

print('== 1. 尝试清 custom_domain ==')
st, b = probe('GET site 当前 cd', 'GET', '/api/v1/sites/%s' % SITE_A)
probe('PATCH custom_domain=null', 'PATCH', '/api/v1/sites/%s' % SITE_A,
      {'custom_domain': None})
st, b = probe('GET 确认', 'GET', '/api/v1/sites/%s' % SITE_A)

print()
print('== 2. deploys 残留状态 ==')
st, b = req('GET', '/api/v1/sites/%s/deploys' % SITE_A)
try:
    for d in json.loads(b):
        print('  deploy %s state=%s id=%s' % (d.get('name'), d.get('state'), d.get('id')))
except Exception as e:
    print('parse err', b[:200])

print()
print('== 3. hooks/build_hooks/dns_zones 残留 ==')
for p in ['/api/v1/hooks?site_id=%s' % SITE_A,
          '/api/v1/sites/%s/build_hooks' % SITE_A,
          '/api/v1/dns_zones',
          '/api/v1/deploy_keys']:
    st, b = req('GET', p)
    try:
        d = json.loads(b)
        n = len(d) if isinstance(d, list) else 'obj'
        print('%-40s %s items=%s' % (p.split('/api/v1')[1], st, n))
    except Exception:
        print('%-40s %s | %s' % (p, st, b[:100]))
print('done')
