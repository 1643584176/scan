# -*- coding: utf-8 -*-
"""清理 storage buckets + PostgREST RLS 变异: upsert/merge/bulk/嵌套 绕过 with check"""
import http.client, ssl, json, time, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
A_EMAIL, A_PASS = 'sbx_auvjijfz@qq.com', 'Sbxtest123!'
B_EMAIL, B_PASS = 'sbx_cwlkmtp@qq.com', 'Sbxtest123!'
A_UID = '37da79f7-2d8a-47e9-9183-5098b80cef8e'
toks = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'r'))
ctx = ssl.create_default_context()
out = []
def call(method, path, body=None, tag='', bearer=None, apikey=ANON_KEY, maxb=8000, retries=2, extra_h=None, raw=False):
    body_j = json.dumps(body) if body is not None and not raw else body
    for i in range(retries):
        c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
        h = {"User-Agent": UA, "Accept": "application/json", "apikey": apikey,
             "Authorization": "Bearer " + (bearer or apikey)}
        if body_j is not None:
            h["Content-Type"] = "text/plain" if raw else "application/json"
        if extra_h:
            h.update(extra_h)
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

# 0. 清理 buckets
call('DELETE', '/storage/v1/bucket/sbx_priv?emptiedBucket=true', None, 'del-bucket-priv', apikey=SR_KEY)
call('DELETE', '/storage/v1/bucket/sbx_pub?emptiedBucket=true', None, 'del-bucket-pub', apikey=SR_KEY)
call('GET', '/storage/v1/bucket', 'buckets-after', apikey=SR_KEY)

# 1. A 登录
st, b = call('POST', '/auth/v1/token?grant_type=password', {"email": A_EMAIL, "password": A_PASS}, 'login-A')
A_TOKEN = re.search(r'"access_token":"([^"]+)"', b).group(1)
B_TOKEN = toks['B_TOKEN']

# ===== RLS 变异 =====
# 2. A upsert 到自己的行 (id=1 是 A 的行; on_conflict=id)
call('POST', '/rest/v1/sbx_rls_t?on_conflict=id', {"id": 1, "secret": "A-UPSERT-OWN"}, 'A-upsert-own',
     bearer=A_TOKEN, extra_h={"Prefer": "resolution=merge-duplicates,return=representation"})
# 3. B upsert 到 A 的行 (id=1) - 经典 with check 绕过尝试
call('POST', '/rest/v1/sbx_rls_t?on_conflict=id', {"id": 1, "secret": "B-UPSERT-STEAL"}, 'B-upsert-A-row',
     bearer=B_TOKEN, extra_h={"Prefer": "resolution=merge-duplicates,return=representation"})
# 4. B 数组批量插入伪造 owner=A (bulk)
call('POST', '/rest/v1/sbx_rls_t', [{"owner": A_UID, "secret": "B-BULK-1"}, {"owner": A_UID, "secret": "B-BULK-2"}],
     'B-bulk-ownerA', bearer=B_TOKEN)
# 5. B update 自己行时把 owner 改成 A (using=自己行 ok; with check 拦?)
call('PATCH', '/rest/v1/sbx_rls_t?secret=eq.B-DATA', {"owner": A_UID}, 'B-upd-owner-self', bearer=B_TOKEN,
     extra_h={"Prefer": "return=representation"})
# 6. A 检查自己的行是否被污染
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'A-final-check', bearer=A_TOKEN)
# 7. B 检查
call('GET', '/rest/v1/sbx_rls_t?select=id,owner,secret', 'B-final-check', bearer=B_TOKEN)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb74_variant.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
