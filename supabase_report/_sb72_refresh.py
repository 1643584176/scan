# -*- coding: utf-8 -*-
"""刷新 A/B tokens + GoTrue settings/health 探针"""
import http.client, ssl, json, time, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
A_EMAIL, A_PASS = 'sbx_auvjijfz@qq.com', 'Sbxtest123!'
B_EMAIL, B_PASS = 'sbx_cwlkmtp@qq.com', 'Sbxtest123!'
ctx = ssl.create_default_context()
out = []
def call(method, path, body=None, tag='', bearer=None, apikey=ANON_KEY, maxb=8000, retries=2, host=HOST):
    body_j = json.dumps(body) if body is not None else None
    for i in range(retries):
        c = http.client.HTTPSConnection(host, timeout=25, context=ctx)
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

# 1. 刷新 A/B (password grant)
st, b = call('POST', '/auth/v1/token?grant_type=password', {"email": A_EMAIL, "password": A_PASS}, 'login-A')
A_TOKEN = re.search(r'"access_token":"([^"]+)"', b).group(1)
A_REF = re.search(r'"refresh_token":"([^"]+)"', b).group(1)
st2, b2 = call('POST', '/auth/v1/token?grant_type=password', {"email": B_EMAIL, "password": B_PASS}, 'login-B')
B_TOKEN = re.search(r'"access_token":"([^"]+)"', b2).group(1)
B_REF = re.search(r'"refresh_token":"([^"]+)"', b2).group(1)
print('A_TOKEN_LEN=%d B_TOKEN_LEN=%d' % (len(A_TOKEN), len(B_TOKEN)))
json.dump({'A_EMAIL': A_EMAIL, 'A_PASS': A_PASS, 'A_TOKEN': A_TOKEN, 'A_REF': A_REF,
           'B_EMAIL': B_EMAIL, 'B_PASS': B_PASS, 'B_TOKEN': B_TOKEN, 'B_REF': B_REF},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'w'))
# 2. GoTrue settings (公开配置面)
call('GET', '/auth/v1/settings', 'settings')
call('GET', '/auth/v1/health', 'health')
# 3. A userinfo 快照
call('GET', '/auth/v1/user', 'A-user', bearer=A_TOKEN)
# 4. B userinfo
call('GET', '/auth/v1/user', 'B-user', bearer=B_TOKEN)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb72_refresh.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
