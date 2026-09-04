# -*- coding: utf-8 -*-
"""窗口期变体测试(全只读):
1. deprecated /users/me/consumption 带参数是否仍执行(shadow behavior)
2. org handle 别名(-org-calm-sound-68506202)是否可路由
3. refcode/referral 相关端点
4. ai_gateway 参数变体(伪造 project_id/org_id 看分层)
"""
import http.client, ssl, re, os, sys, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST
m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)
O = 'org-calm-sound-68506202'
PID = 'jolly-term-94460232'

def req(path, csrf=True):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = CSRF
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, 'EXC %s' % e

def show(tag, p):
    st, b = req(p)
    print('%s %-78s %s %s' % (tag, p, st, b[:380].replace('\n', ' ')), flush=True)
    time.sleep(0.15)

# probe
st, b = req('/api/v2/users/me')
print('PROBE:', st, flush=True)
if st != 200:
    sys.exit(1)

print('=== deprecated consumption 变体 ===', flush=True)
show('D', '/api/v2/users/me/consumption?from=2026-09-01&to=2026-09-05')
show('D', '/api/v2/users/me/consumption?period=current')
show('D', '/api/v2/users/me/consumption?project_id=%s' % PID)

print('=== org handle/别名 ===', flush=True)
show('H', '/api/v2/organizations/-org-calm-sound-68506202')
show('H', '/api/v2/organizations/org-calm-sound-68506202/consumption')
show('H', '/api/v2/organizations/-org-calm-sound-68506202/members?limit=5')

print('=== refcode / referral ===', flush=True)
for p in ['/api/v2/users/me/refcode',
          '/api/v2/referrals?ref_code=BPL1967A',
          '/api/v2/users/me/referrals',
          '/api/v2/refcode/BPL1967A',
          '/api/v2/registration/referral?ref_code=BPL1967A']:
    show('R', p)

print('=== ai_gateway 参数变体分层 ===', flush=True)
show('A', '/api/v2/ai_gateway/models?project_id=does-not-exist-000000')
show('A', '/api/v2/ai_gateway/models?project_id=%s' % PID)
show('A', '/api/v2/ai_gateway/models?project_id=%s&org_id=%s' % (PID, O))
show('A', '/api/v2/ai_gateway/models?org_id=%s' % O)

print('=== mfa/session 杂项 ===', flush=True)
show('X', '/api/v2/users/me/mfa/totp/removal')
show('X', '/api/v2/users/me/detach_social_link')
show('X', '/api/v2/users/me/password/validate')
print('DONE', flush=True)
