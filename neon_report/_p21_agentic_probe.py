# -*- coding: utf-8 -*-
"""agentic account_requests 端点黑盒语义:
orchestrator 候选 × id 候选 -> 404/401/403 分层 + id 格式/错误信息"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def ctl_req(method, path, body=None):
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
    if body is not None:
        hdrs['Content-Type'] = 'application/json'
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    conn3.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

ORCHS = ['mcp', 'claude', 'cursor', 'openai', 'github', 'copilot', 'agent', 'neon', 'supabase', 'v0', 'replit', 'windsurf']
IDS = ['1', 'abc', '00000000-0000-0000-0000-000000000000', 'test']

for o in ORCHS:
    for i in IDS[:2]:
        st, raw = ctl_req('GET', API_BASE + '/agentic_provisioning/account_requests/%s/%s' % (o, i))
        msg = raw[:150].replace('\n', ' ')
        print('%s/%s -> %d %s' % (o, i, st, msg), flush=True)
        time.sleep(0.2)
    if st == 404:
        print('  ... (orchestrator %s all 404)' % o, flush=True)
        break
