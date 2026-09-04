# -*- coding: utf-8 -*-
"""PROD 只读面一键补全(会话窗口短, 拿到新 cookie 立即跑, <2min):
org 面 + users 面 + ai_gateway 全量 + add-ons 变体 + 响应头 Set-Cookie 观察
"""
import http.client, ssl, re, os, sys, json, time

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)
O = 'org-calm-sound-68506202'
PID = 'jolly-term-94460232'

def req(path, csrf=True, method='GET', body=None, show_hdr=False):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = CSRF
        conn.request(method, path, headers=h, body=body)
        r = conn.getresponse()
        sc = r.getheader('Set-Cookie', '')
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw, sc
    except Exception as e:
        return -1, 'EXC %s' % e, ''

def show(tag, p, method='GET', body=None):
    st, b, sc = req(p, True, method, body)
    extra = (' | SC:%s' % sc[:80]) if sc else ''
    print('%s %-70s %s %s%s' % (tag, p, st, b[:450].replace('\n', ' '), extra), flush=True)
    time.sleep(0.15)
    return st, b

# 会话探针
st, b, _ = req('/api/v2/users/me')
print('PROBE users/me:', st, b[:120], flush=True)
if st != 200:
    print('SESSION DEAD - stop', flush=True)
    sys.exit(1)

print('=== org 面 ===', flush=True)
for p in ['/api/v2/organizations/%s' % O,
          '/api/v2/organizations/%s/members?limit=20' % O,
          '/api/v2/organizations/%s/invitations' % O,
          '/api/v2/organizations/%s/guests' % O,
          '/api/v2/organizations/%s/domains' % O,
          '/api/v2/organizations/%s/sso' % O,
          '/api/v2/organizations/%s/sso/enforcement' % O,
          '/api/v2/organizations/%s/api_keys' % O,
          '/api/v2/organizations/%s/early_access' % O,
          '/api/v2/organizations/%s/consumption?from=2026-09-01&to=2026-09-05' % O,
          '/api/v2/organizations/%s/deletion_checklist' % O]:
    show('O', p)

print('=== users 面 ===', flush=True)
for p in ['/api/v2/users/me/auth',
          '/api/v2/users/me/refcode',
          '/api/v2/users/me/consumption',
          '/api/v2/users/me/memberships',
          '/api/v2/users/me/deletion_checklist',
          '/api/v2/users/me/early_access']:
    show('U', p)

print('=== ai_gateway 全量 ===', flush=True)
st, b = show('A', '/api/v2/ai_gateway/models?project_id=%s&org_id=%s' % (PID, O))
try:
    d = json.loads(b)
    ms = d.get('models', [])
    en = [x for x in ms if x.get('enabled')]
    print('  models total=%d enabled=%d' % (len(ms), len(en)), flush=True)
    print('  enabled list:', [(x['id'], x.get('provider')) for x in en][:30], flush=True)
    open(os.path.join(here, '_p86_models.json'), 'w', encoding='utf-8').write(json.dumps(d, indent=1))
except Exception as e:
    print('  parse err', e, flush=True)

print('=== add-ons 变体 / 杂项 ===', flush=True)
for p in ['/api/v2/add-ons',
          '/api/v2/add-ons/active',
          '/api/v2/organizations/%s/add-ons/active' % O,
          '/api/v2/users/me/mfa',
          '/api/v2/users/me/mfa/totp',
          '/api/v2/users/me/mfa/passkey',
          '/api/v2/system/status/summary',
          '/api/v2/healthz',
          '/api/v2/analytics/high_fit',
          '/api/v2/applications?org_id=%s' % O]:
    show('M', p)
print('DONE', flush=True)
