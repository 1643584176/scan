# -*- coding: utf-8 -*-
"""建 project C(同主账号) + 确认 storage enabled + 记录 C 的 bid/bucket"""
import http.client, ssl, json, re, html, os, sys, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def csrf_cookie():
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    return '; '.join(parts), csrf

def ctl(method, path, body=None):
    ck, csrf = csrf_cookie()
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    hdrs = {'Cookie': ck, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf,
            'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    raw = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, raw

# 1) 建 C 项目(us-east-2)
st, raw = ctl('POST', '/projects', {'project': {'name': 'sec-cross-store-' + str(int(time.time()))[-6:],
                                                 'region_id': 'aws-us-east-2', 'pg_version': 17}})
print('create -> %d %s' % (st, raw[:500].replace('\n', ' ')), flush=True)
try:
    d = json.loads(raw)
    pid = d['project']['id']
    bids = [b['id'] for b in d.get('branches', [])]
    print('PID:', pid, 'BID:', bids, flush=True)
    # 保存 ctx_c.json
    import io as _io
    _io.open('_ctx_c.json', 'w', encoding='utf-8').write(json.dumps({'pid': pid, 'bid': bids[0] if bids else ''}))
except Exception as e:
    print('parse err:', e, flush=True)
    raise SystemExit

# 2) 等几秒再查 storage/AI 状态
time.sleep(5)
for path in ['/projects/%s/branches/%s/storage' % (pid, bids[0]),
             '/projects/%s/branches/%s/ai_gateway' % (pid, bids[0])]:
    st, raw = ctl('GET', path)
    print('GET %s -> %d %s' % (path.split('/')[-1], st, raw[:400].replace('\n', ' ')), flush=True)
