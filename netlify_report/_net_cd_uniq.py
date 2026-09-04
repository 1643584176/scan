# -*- coding: utf-8 -*-
"""custom_domain unique 检查语义实验(临时站点,测完即删)
问题: *.example.com 全报 must be unique —— 是全名唯一?注册域唯一?解绑残留?
"""
import http.client, ssl, gzip, brotli, json, sys, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

def req(method, path, body=None, timeout=30):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A}
    b = json.dumps(body).encode() if body is not None else None
    t0 = time.time()
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    dt = time.time() - t0
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, dt, txt

def mk_site():
    name = 'sec-uniq-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    st, dt, b = req('POST', '/api/v1/sites', {'name': name})
    try:
        return st, json.loads(b).get('id')
    except Exception:
        return st, b[:100]

def del_site(sid):
    st, dt, b = req('DELETE', '/api/v1/sites/' + sid)
    return st

def patch_cd(sid, val):
    st, dt, b = req('PATCH', '/api/v1/sites/' + sid, {'custom_domain': val})
    try:
        j = json.loads(b)
        if st == 200:
            return st, 'ACCEPT cd=%r' % j.get('custom_domain')
        err = j.get('errors') or j.get('message') or j.get('code')
        return st, str(err)[:110]
    except Exception:
        return st, b[:110]

r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
print('rand =', r)

cases = [
    ('A 绑 root-%s.com(全新注册域)' % r,      'root-%s.com' % r),
    ('B 绑 sub.root-%s.com(同注册域)' % r,    'sub.root-%s.com' % r),
    ('C 绑 other-%s.com(对照)' % r,           'other-%s.com' % r),
    ('D 绑 attacker-controlled.com(今日解绑过)', 'attacker-controlled.com'),
    ('E 绑 re-%s.example.com(example.com 家族)' % r, 're-%s.example.com' % r),
    ('F 绑 www-%s.co.uk(双段后缀)' % r,       'www-%s.co.uk' % r),
]

sites = []
for label, dom in cases:
    st, sid = mk_site()
    if st not in (200, 201) or not isinstance(sid, str):
        print('mk fail:', st, sid)
        break
    sites.append((label, sid))
    print('created', label.split(' ')[0], sid)

for label, sid in sites:
    dom = dict((l.split(' ')[0], d) for l, d in cases)[label.split(' ')[0]]
    print('%-42s -> %s' % (label, patch_cd(sid, dom)))

print()
print('== 清理: 删除全部临时站点 ==')
for label, sid in sites:
    st = del_site(sid)
    print('del', label.split(' ')[0], sid, '->', st)
print('done')
