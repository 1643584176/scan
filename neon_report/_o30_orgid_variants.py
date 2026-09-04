# -*- coding: utf-8 -*-
"""create project org_id 参数位置矩阵"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def csrf_cookie(cookie):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie.split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    return '; '.join(parts), csrf

ORG = 'org-flat-dawn-91601224'
PROJ = {'name': 'sec-cross-store-' + str(int(time.time()))[-6:], 'region_id': 'aws-us-east-2', 'pg_version': 17}

def ctl(path, body=None, extra_hdrs=None):
    ck, csrf = csrf_cookie(cookie_str())
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    hdrs = {'Cookie': ck, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf,
            'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if extra_hdrs:
        hdrs.update(extra_hdrs)
    conn.request('POST', API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    raw = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, raw

tests = [
    ('body org_id top', '/projects', {'org_id': ORG, 'project': PROJ}),
    ('body organization_id', '/projects', {'organization_id': ORG, 'project': PROJ}),
    ('query org_id', '/projects?org_id=' + ORG, {'project': PROJ}),
    ('query organization_id', '/projects?organization_id=' + ORG, {'project': PROJ}),
    ('project.settings.org', '/projects', {'project': dict(PROJ, settings={'org_id': ORG})}),
]
for name, path, body in tests:
    st, raw = ctl(path, body)
    ok = 'created' if st in (200, 201) else ''
    print('[%s] %d %s %s' % (name, st, raw[:200].replace('\n', ' '), ok), flush=True)
    if st in (200, 201):
        # 建成了就停(拿到了)后续单独清理
        try:
            d = json.loads(raw)
            import io as _io
            _io.open('_ctx_c.json', 'w', encoding='utf-8').write(
                json.dumps({'pid': d['project']['id'],
                            'bid': [b['id'] for b in d.get('branches', [])][0]}))
            print('SAVED PID', d['project']['id'], flush=True)
        except Exception:
            pass
        break
    time.sleep(1)

# header 变体(仅当 body 全失败)
else:
    for name, hdr in [('X-Org-Id', {'X-Org-Id': ORG}), ('Neon-Org-Id', {'Neon-Org-Id': ORG})]:
        st, raw = ctl('/projects', {'project': PROJ}, extra_hdrs=hdr)
        print('[%s] %d %s' % (name, st, raw[:200].replace('\n', ' ')), flush=True)
        if st in (200, 201):
            break
