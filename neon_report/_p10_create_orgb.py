# -*- coding: utf-8 -*-
"""建 org B(body: organization + subscription_type)"""
import http.client, ssl, json, re, html, sys, os, time, uuid

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def ctl_req(method, path, body=None, referer=None):
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
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if referer:
        hdrs['Referer'] = referer
    if body is not None:
        hdrs['Content-Type'] = 'application/json'
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    conn3.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

REF = 'https://console-stage.neon.build/'
suffix = uuid.uuid4().hex[:4]
variants = [
    {'organization': {'name': 'sec-orgb-%s' % suffix}, 'subscription_type': 'free'},
    {'organization': {'name': 'sec-orgb-%s' % suffix, 'handle': 'sec-orgb-%s' % suffix}, 'subscription_type': 'free'},
    {'name': 'sec-orgb-%s' % suffix, 'subscription_type': 'free', 'handle': 'sec-orgb-%s' % suffix},
]
for i, body in enumerate(variants):
    st, raw = ctl_req('POST', API_BASE + '/organizations', body, referer=REF)
    print('[%d] %s -> %d %s' % (i, json.dumps(body)[:120], st, raw[:300]), flush=True)
    try:
        oid = json.loads(raw).get('id') or (json.loads(raw).get('organization') or {}).get('id')
        if oid:
            open('D:/scan/neon_report/_orgb.json', 'w').write(json.dumps({'org_b': oid}))
            print('ORG_B = %s' % oid, flush=True)
            break
    except Exception:
        pass
    time.sleep(0.5)
