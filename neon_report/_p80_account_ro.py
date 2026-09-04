# -*- coding: utf-8 -*-
"""1. GET / 完整保存, 提取 org/account 上下文
2. 账号级只读端点批量探测(全 GET, 零写)
"""
import http.client, ssl, re, os, sys, time

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)

def req(path, csrf=None, extra_h=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = csrf
        if extra_h:
            h.update(extra_h)
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, 'EXC %s' % e

# 1. 首页 -> 找 org
st, body = req('/', CSRF)
open(os.path.join(here, '_p80_home.html'), 'w', encoding='utf-8').write(body)
print('home status', st, 'len', len(body), flush=True)
# org 相关: 各种 id 形态
for pat in ['org-calm[^"\\s<]*', 'calm-sound[^"\\s<]*', r'"id":"[0-9a-f-]{36}"', 'ORGANIZATION[^<]{0,120}', 'organizationId[^,]{0,120}']:
    hits = set(re.findall(pat, body))
    print('PAT', pat, '->', list(hits)[:12], flush=True)

# csrf from page (unmasked?)
mc = re.search(r'"csrf":"([^"]+)"', body)
print('page csrf:', mc.group(1)[:80] if mc else None, flush=True)

print('=== 2. 只读批量探测 ===', flush=True)
tests = [
    '/api/v2/add-ons/active',
    '/api/v2/add-ons/history',
    '/api/v2/users/me/memberships',
    '/api/v2/users/me/feature_flags',
    '/api/v2/users/me/early_access',
    '/api/v2/users/me/mfa',
    '/api/v2/system/status/summary',
    '/api/v2/analytics/high_fit',
    '/api/v2/ai_gateway/models',
    '/api/v2/ai_gateway/resolve_identity',
    '/api/v2/applications',
    '/api/v2/migration/checklist',
    '/api/v2/organizations/org-calm-sound-68506202/consumption',
    '/api/v2/organizations/org-calm-sound-68506202/limits',
    '/api/v2/organizations/org-calm-sound-68506202/deletion_checklist',
    '/api/v2/organizations/org-calm-sound-68506202/feature_flags',
    '/api/v2/organizations/org-calm-sound-68506202/early_access',
    '/api/v2/projects/count',
    '/api/v2/projects/usage-status',
]
for p in tests:
    st2, b2 = req(p, CSRF)
    print('%-70s %s %s' % (p, st2, b2[:300].replace('\n', ' ')), flush=True)
    time.sleep(0.25)
