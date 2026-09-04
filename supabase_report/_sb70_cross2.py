# -*- coding: utf-8 -*-
"""租户隔离交叉测试 v2: apikey=anon 固定 + Authorization 区分身份"""
import http.client, ssl, json, time, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
A_EMAIL, A_PASS = 'sbx_auvjijfz@qq.com', 'Sbxtest123!'
toks = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'r'))
ctx = ssl.create_default_context()
out = []
def call(method, path, body=None, tag='', bearer=None, apikey=ANON_KEY, maxb=6000, retries=2):
    body_j = json.dumps(body) if body is not None else None
    for i in range(retries):
        c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
        h = {"User-Agent": UA, "Accept": "application/json", "apikey": apikey,
             "Authorization": "Bearer " + (bearer or apikey)}
        if body_j:
            h["Content-Type"] = "application/json"
        h.update(VDP_HEADERS)
        t0 = time.time()
        try:
            c.request(method, path, headers=h, body=body_j)
            r = c.getresponse()
            b = r.read(maxb).decode('utf-8', errors='replace')
            out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1500]))
            c.close()
            return r.status, b
        except Exception as e:
            out.append('### [%s] %s %s try%d ERR %s' % (tag, method, path, i + 1, e))
            time.sleep(1.5)
    return 0, ''

# 0. A/B 重新登录 (刷新 token)
st, b = call('POST', '/auth/v1/token?grant_type=password', {"email": A_EMAIL, "password": A_PASS}, 'login-A')
A_TOKEN = re.search(r'"access_token":"([^"]+)"', b).group(1)
print('A_TOKEN_LEN=%d' % len(A_TOKEN))
# 1. A 插入自己的行 (默认 owner=auth.uid())
call('POST', '/rest/v1/sbx_rls_t', {"secret": "A-DATA-topsecret-7f3a"}, 'A-insert', bearer=A_TOKEN)
# 2. A 读自己 (应 1 行)
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'A-read', bearer=A_TOKEN)
# 3. B 读 (隔离: 应 0 行)
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'B-read', bearer=toks['B_TOKEN'])
# 4. B update A 的行
call('PATCH', '/rest/v1/sbx_rls_t?secret=eq.A-DATA-topsecret-7f3a', {"secret": "HACKED-B"}, 'B-update-A', bearer=toks['B_TOKEN'])
# 5. B delete A 的行
call('DELETE', '/rest/v1/sbx_rls_t?secret=eq.A-DATA-topsecret-7f3a', None, 'B-del-A', bearer=toks['B_TOKEN'])
# 6. B 插入 owner=A 的行 (with check 阻止)
call('POST', '/rest/v1/sbx_rls_t', {"owner": "37da79f7-2d8a-47e9-9183-5098b80cef8e", "secret": "B-claim-A"}, 'B-ins-ownerA', bearer=toks['B_TOKEN'])
# 7. B 正常插入 (应成功)
call('POST', '/rest/v1/sbx_rls_t', {"secret": "B-DATA"}, 'B-insert', bearer=toks['B_TOKEN'])
# 8. anon 读 (无 JWT: 应 0 行)
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'anon-read')
# 9. service_role 读 (绕过 RLS: 全量)
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'sr-read', apikey=SR_KEY)
# 10. A 复查 (自己行仍在)
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'A-read2', bearer=A_TOKEN)
# 11. B 复查 (只自己行)
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'B-read2', bearer=toks['B_TOKEN'])

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb70_cross2.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
