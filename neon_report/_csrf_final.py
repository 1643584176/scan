# -*- coding: utf-8 -*-
"""最终流程:GET / 提取 meta csrf-token -> POST /projects"""
import http.client, ssl, json, sys, re, html
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

# 1. GET / 拿 meta csrf-token + 最新 cookie(含服务器刷新的 _gorilla_csrf)
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
r = conn.getresponse(); body = r.read()
fresh_cookies = {}
for sc in r.headers.get_all('Set-Cookie') or []:
    m = re.match(r'([^=]+)=([^;]*)', sc)
    if m:
        fresh_cookies[m.group(1)] = m.group(2)
conn.close()
print('fresh set-cookies:', list(fresh_cookies.keys()))

txt = body.decode('utf-8', 'replace')
m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
if not m:
    print('NO csrf meta'); sys.exit(1)
csrf_meta = html.unescape(m.group(1))
print('csrf meta len:', len(csrf_meta))

# 2. 组合 cookie:旧 cookie 全量保留,仅当服务器刷新了 _gorilla_csrf 时替换
parts = []
for c in cookie_str().split(';'):
    c = c.strip()
    if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh_cookies:
        parts.append('_gorilla_csrf=' + fresh_cookies['_gorilla_csrf'])
    else:
        parts.append(c)
merged = '; '.join(parts)

# 3. POST
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
     'Cookie': merged}
h.update(HEADERS_TEST)
h['X-CSRF-Token'] = csrf_meta
conn.request('POST', API_BASE + '/projects?org_id=%s' % ORG,
             body=json.dumps({'project': {'name': 'sec-pccp-1'}}).encode(), headers=h)
r = conn.getresponse(); raw = r.read()
st = r.status; conn.close()
print('POST /projects ->', st)
try:
    d = json.loads(raw)
    print(json.dumps(d, indent=1, ensure_ascii=False)[:800])
    pid = d.get('project', {}).get('id')
    print('PID:', pid)
    # 存 pid
    if pid:
        open(r'D:\scan\neon_report\_ctx.json', 'w').write(json.dumps({'pid': pid, 'csrf': csrf_meta}))
except Exception:
    print(raw[:300])
