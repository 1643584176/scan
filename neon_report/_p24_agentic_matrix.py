# -*- coding: utf-8 -*-
"""agentic 审批面深挖矩阵(全部零破坏,探测语义分层):
A. 认证顺序: 无 cookie GET/POST approve -> 401 vs 404(先认证 or 先查资源?)
B. orchestrator 宽枚举: 404 分层 -> 服务商路由表差异(SSRF/上游拼接 oracle)
C. id 格式: uuid/数字/超长/编码斜杠 -> 解析器行为
D. 方法/子路径变体: approve/deny/cancel/reject/revoke/DELETE/PATCH
E. approve body 变体: 空/带参数/带 approved 标志
"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def _req(method, path, body=None, with_auth=True):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
        conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
        r = conn.getresponse(); r.read()
        fresh = {}
        for sc in r.headers.get_all('Set-Cookie') or []:
            m = re.match(r'([^=]+)=([^;]*)', sc)
            if m: fresh[m.group(1)] = m.group(2)
        conn.close()
        conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
        conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
        r2 = conn2.getresponse(); txt = r2.read().decode('utf-8', 'replace'); conn2.close()
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
        csrf = html.unescape(m.group(1)) if m else None
        parts = []
        for c in cookie_str().split(';'):
            c = c.strip()
            if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
                parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
            else:
                parts.append(c)
        conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
        hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
        hdrs.update(HEADERS_TEST)
        if body is not None:
            hdrs['Content-Type'] = 'application/json'
        if csrf:
            hdrs['X-CSRF-Token'] = csrf
        if not with_auth:
            hdrs = {'User-Agent': 'Mozilla/5.0'}
            if body is not None:
                hdrs['Content-Type'] = 'application/json'
        conn3.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
        r3 = conn3.getresponse()
        out = r3.read().decode('utf-8', 'ignore')
        conn3.close()
        return r3.status, out
    except Exception as e:
        return -1, 'EXC %s' % e

B = API_BASE + '/agentic_provisioning/account_requests'
ZERO = '00000000-0000-0000-0000-000000000000'

print('=== A. 认证顺序 ===', flush=True)
for m, p in [('GET', '%s/mcp/%s' % (B, ZERO)),
             ('POST', '%s/mcp/%s/approve' % (B, ZERO))]:
    st, raw = _req(m, p, with_auth=False)
    print('[noauth %s %s] -> %d %s' % (m, p.split('/agentic')[-1], st, raw[:130].replace('\n', ' ')), flush=True)
st, raw = _req('GET', '%s/mcp/%s' % (B, ZERO))
print('[auth GET] -> %d %s' % (st, raw[:130].replace('\n', ' ')), flush=True)

print('\n=== B. orchestrator 宽枚举(GET + zero uuid) ===', flush=True)
orchs = ['mcp', 'MCP', 'Mcp', 'mcp ', ' mcp', 'anthropic', 'openai', 'github', 'copilot',
         'cursor', 'slack', 'vercel', 'zed', 'claude', 'claude-code', 'codex', 'agent',
         'browser', 'assistant', 'v0', 'lovable', 'bolt', 'manus', 'windsurf', 'replit',
         'craft', 'devon', 'google', 'aws', 'azure', 'mcp/..', 'mcp%2f..', '..', '%2e%2e',
         'mcp/../../..', 'mcp?x=1', 'mcp#f', 'MCP2', 'mcp2', 'neon-mcp', 'neon_mcp',
         'other', 'unknown', 'test', 'mcp/1', '1', '0']
seen = {}
for o in orchs:
    st, raw = _req('GET', '%s/%s/%s' % (B, o, ZERO))
    key = st
    msg = raw[:110].replace('\n', ' ')
    if key not in seen:
        seen[key] = (o, msg)
    print('%-14s -> %d %s' % (o[:13], st, msg), flush=True)
    time.sleep(0.12)
print('状态分布:', {k: v[0] for k, v in seen.items()}, flush=True)

print('\n=== C. id 格式(固定 orchestrator=mcp) ===', flush=True)
ids = [ZERO, '1', '0', '-1', 'abc', 'a' * 64, 'a' * 500, '..', '%2e%2e',
       ZERO + '/..', 'x' + ZERO, ZERO.upper(),
       '11111111-1111-1111-1111-111111111111',
       'ffffffff-ffff-ffff-ffff-ffffffffffff']
for i in ids:
    st, raw = _req('GET', '%s/mcp/%s' % (B, i))
    print('%-40s -> %d %s' % (i[:39], st, raw[:110].replace('\n', ' ')), flush=True)
    time.sleep(0.12)

print('\n=== D. 方法/子路径(固定 mcp + zero uuid) ===', flush=True)
for m, suffix in [('POST', '/approve'), ('POST', '/deny'), ('POST', '/cancel'),
                  ('POST', '/reject'), ('POST', '/revoke'), ('DELETE', ''),
                  ('PATCH', ''), ('PUT', ''), ('POST', ''), ('POST', '/approve/'),
                  ('GET', '/approve'), ('GET', '/pending'), ('GET', '/list'),
                  ('POST', '/approve?x=1'), ('POST', '/approve/../../approve')]:
    p = '%s/mcp/%s%s' % (B, ZERO, suffix)
    st, raw = _req(m, p)
    print('[%s %s] -> %d %s' % (m, suffix or '/', st, raw[:110].replace('\n', ' ')), flush=True)
    time.sleep(0.12)

print('\n=== E. approve body 变体(POST 零 uuid) ===', flush=True)
bodies = [None, {}, {'approved': True}, {'approved': False}, {'decision': 'approve'},
          {'org_id': 'x'}, {'project_id': 'x'}, {'grant': {'scope': 'all'}}]
for b in bodies:
    st, raw = _req('POST', '%s/mcp/%s/approve' % (B, ZERO), body=b)
    print('[body %s] -> %d %s' % (str(b)[:40], st, raw[:110].replace('\n', ' ')), flush=True)
    time.sleep(0.12)
