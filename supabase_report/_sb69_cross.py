# -*- coding: utf-8 -*-
"""租户隔离交叉测试: A 插入 -> B/anon 越权尝试 -> 视图/函数等绕过面标记"""
import http.client, ssl, json, time, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
A_EMAIL, A_PASS = 'sbx_auvjijfz@qq.com', 'Sbxtest123!'
toks = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'r'))
B_EMAIL, B_PASS, B_ID = toks['B_EMAIL'], toks['B_PASS'], toks['B_ID']
ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', key=ANON_KEY, maxb=6000):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "apikey": key,
         "Authorization": "Bearer " + key}
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1800]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 0. A 重新登录拿 token
st, b = req('POST', '/auth/v1/token?grant_type=password', {"email": A_EMAIL, "password": A_PASS}, 'login-A')
m = re.search(r'"access_token":"([^"]+)"', b)
A_TOKEN = m.group(1) if m else ''
print('A_TOKEN_LEN=%d' % len(A_TOKEN))
T = lambda t: {"apikey": ANON_KEY, "Authorization": "Bearer " + t}
# 1. A 插入自己的行
req('POST', '/rest/v1/sbx_rls_t', {"secret": "A-DATA-topsecret"}, 'A-insert', key=A_TOKEN)
# 2. A 读自己 (应 1 行)
req('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'A-read', key=A_TOKEN)
# 3. B 读 A 的行 (RLS 隔离: 应 0 行)
req('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'B-read-A', key=toks['B_TOKEN'])
# 4. B 尝试 update A 的行
req('PATCH', '/rest/v1/sbx_rls_t?secret=eq.A-DATA-topsecret', {"secret": "HACKED-B"}, 'B-update-A', key=toks['B_TOKEN'])
# 5. B 尝试 delete A 的行
req('DELETE', '/rest/v1/sbx_rls_t?secret=eq.A-DATA-topsecret', None, 'B-del-A', key=toks['B_TOKEN'])
# 6. B 插入 owner=A 的行 (with check 阻止)
req('POST', '/rest/v1/sbx_rls_t', {"owner": "37da79f7-2d8a-47e9-9183-5098b80cef8e", "secret": "B-claim-A"}, 'B-ins-ownerA', key=toks['B_TOKEN'])
# 7. B 正常插入 (应成功, owner=B)
req('POST', '/rest/v1/sbx_rls_t', {"secret": "B-DATA"}, 'B-insert', key=toks['B_TOKEN'])
# 8. anon 读 (应 0/403)
req('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'anon-read', key=ANON_KEY)
# 9. service_role 读 (绕过 RLS: 全量)
req('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'sr-read', key=SR_KEY)
# 10. A 复查 (自己 1 行 + B 不可见)
req('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'A-read2', key=A_TOKEN)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb69_cross.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
