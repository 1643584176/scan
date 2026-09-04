# -*- coding: utf-8 -*-
"""deploy_keys 创建后跨账号可读性测试: A 创建 -> A/B/anon 读 -> 清理
附: ai-gateway token claims 解码
"""
import http.client, ssl, gzip, brotli, json, sys, base64
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=20):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body is not None else None
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

print('== 1. A 创建 deploy key ==')
st, b = req('POST', '/api/v1/deploy_keys', {}, TOKEN_A)
print(st, b[:300])
kid = None
try:
    j = json.loads(b)
    kid = j.get('id')
    print('key id =', kid)
except Exception:
    pass

print()
print('== 2. 创建后读取对比 ==')
for tag, tok in [('A 自己', TOKEN_A), ('B 跨账号', TOKEN_B), ('匿名', None)]:
    st, b = req('GET', '/api/v1/deploy_keys', token=tok)
    print('%-10s %s | %s' % (tag, st, b[:300]))

print()
print('== 3. 单个 key 读取 ==')
if kid:
    for tag, tok in [('A 自己', TOKEN_A), ('B 跨账号', TOKEN_B)]:
        st, b = req('GET', '/api/v1/deploy_keys/' + kid, token=tok)
        print('%-10s %s | %s' % (tag, st, b[:200]))
    print('清理:')
    st, b = req('DELETE', '/api/v1/deploy_keys/' + kid, token=TOKEN_A)
    print('  del:', st, b[:100])
    st, b = req('GET', '/api/v1/deploy_keys', token=TOKEN_A)
    print('  after del:', st, b[:100])

print()
print('== 4. ai-gateway token claims 解码(A 自己的)==')
st, b = req('GET', '/api/v1/sites/%s/ai-gateway/token' % SITE_A, token=TOKEN_A)
try:
    j = json.loads(b)
    tok = j.get('token', '')
    parts = tok.split('.')
    if len(parts) >= 2:
        hdr = base64.urlsafe_b64decode(parts[0] + '==')
        pay = base64.urlsafe_b64decode(parts[1] + '==')
        print('header:', hdr.decode('utf-8', 'ignore'))
        print('claims:', pay.decode('utf-8', 'ignore'))
except Exception as e:
    print('decode fail', e, b[:200])
print('done')
