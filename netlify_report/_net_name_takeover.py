# -*- coding: utf-8 -*-
"""site name 冲突语义: 同名创建 / 跨账号抢占 / 删除释放(netlify.app 子域接管面)"""
import http.client, ssl, gzip, brotli, json, sys, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()

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

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-58s %s | %s' % (tag, st, b[:240].replace('\n', ' ')))
    return st, b

rnd = ''.join(random.choices(string.ascii_lowercase, k=8))
NAME1 = 'zz-name-%s' % rnd

print('== 1. A 创建站点 name=%s ==' % NAME1)
st, b = probe('A POST sites', 'POST', '/api/v1/sites', {'name': NAME1})
sid1 = None
try:
    sid1 = json.loads(b).get('id')
    print('  site id:', sid1, ' default_domain 字段在响应:', 'default_domain' in b)
except Exception:
    pass

print()
print('== 2. 同 account 二次同名创建 ==')
st, b = probe('A POST sites 同名', 'POST', '/api/v1/sites', {'name': NAME1})

print()
print('== 3. B 跨账号抢占同名 ==')
st, b = probe('B POST sites 同名', 'POST', '/api/v1/sites', {'name': NAME1}, TOKEN_B)
sid2 = None
try:
    d = json.loads(b)
    if 'id' in d:
        sid2 = d['id']
        print('  B 创建成功! site id:', sid2)
except Exception:
    pass

print()
print('== 4. 若 B 成功: 谁的子域生效 ==')
if sid2:
    for host in ['%s.netlify.app' % NAME1, '%s.netlify.app' % NAME1]:
        try:
            st, bb = req('GET', '/', None, None, host=host)
            print('GET %s -> %s | %s' % (host, st, bb[:200].replace('\n', ' ')))
        except Exception as e:
            print(host, 'ERR', e)

print()
print('== 5. 清理 ==')
for sid in [sid1, sid2]:
    if sid:
        st, b = probe('DELETE site %s' % sid[:8], 'DELETE', '/api/v1/sites/%s' % sid)
        if st == 204:
            time.sleep(1)
            st2, b2 = probe('  同名立即重建(释放语义)', 'POST', '/api/v1/sites', {'name': NAME1})
            if st2 in (200, 201):
                sid3 = json.loads(b2).get('id')
                req('DELETE', '/api/v1/sites/%s' % sid3)
                print('  重建成功并已删(删除后立即释放)')
print('done')
