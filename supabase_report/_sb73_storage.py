# -*- coding: utf-8 -*-
"""Storage 面: private bucket 隔离 + authenticated 上传/读 + anon 面 (2026 新 storage 行为)"""
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
def call(method, path, body=None, tag='', bearer=None, apikey=ANON_KEY, maxb=8000, retries=2, raw=False):
    body_j = json.dumps(body) if body is not None and not raw else body
    for i in range(retries):
        c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
        h = {"User-Agent": UA, "Accept": "application/json", "apikey": apikey,
             "Authorization": "Bearer " + (bearer or apikey)}
        if body_j is not None:
            if raw:
                h["Content-Type"] = "text/plain"
            else:
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

def login(email, pw, tag):
    st, b = call('POST', '/auth/v1/token?grant_type=password', {"email": email, "password": pw}, tag)
    return re.search(r'"access_token":"([^"]+)"', b).group(1)

A_TOKEN = login(A_EMAIL, A_PASS, 'login-A')
B_TOKEN = login(B_EMAIL, B_PASS, 'login-B')
print('tokens ok')

# 1. sr 建 private bucket (2026 storage)
call('POST', '/storage/v1/bucket', {"name": "sbx_priv", "id": "sbx_priv", "public": False}, 'sr-mk-bucket', apikey=SR_KEY)
# 2. sr 上传对象
call('POST', '/storage/v1/object/sbx_priv/sr_file.txt', "SR-CONTENT-9f3a", 'sr-upload', apikey=SR_KEY, raw=True)
# 3. A 上传 (authenticated 无 policy -> 应 403 或 201?)
call('POST', '/storage/v1/object/sbx_priv/a_file.txt', "A-CONTENT", 'A-upload', bearer=A_TOKEN, raw=True)
# 4. A 列 bucket 内对象
call('POST', '/storage/v1/object/list/sbx_priv', {"prefix": "", "limit": 100}, 'A-list', bearer=A_TOKEN)
# 5. A 读 sr 文件 (下载)
call('GET', '/storage/v1/object/sbx_priv/sr_file.txt', None, 'A-get-srfile', bearer=A_TOKEN)
# 6. anon 读 sr 文件
call('GET', '/storage/v1/object/sbx_priv/sr_file.txt', None, 'anon-get-srfile')
# 7. sr 建 public bucket
call('POST', '/storage/v1/bucket', {"name": "sbx_pub", "id": "sbx_pub", "public": True}, 'sr-mk-pub', apikey=SR_KEY)
# 8. sr 上传 public 对象
call('POST', '/storage/v1/object/sbx_pub/pub_file.txt', "PUB-CONTENT", 'sr-upload-pub', apikey=SR_KEY, raw=True)
# 9. anon 读 public 对象 (无 RLS policy 时应 400/404? storage 公开读需要 policy 或 public bucket 默认允许?)
call('GET', '/storage/v1/object/public/sbx_pub/pub_file.txt', None, 'anon-get-pub')
# 10. A 上传到 public bucket
call('POST', '/storage/v1/object/sbx_pub/a_pub.txt', "A-PUB", 'A-upload-pub', bearer=A_TOKEN, raw=True)
# 11. bucket 列表 (A 视角)
call('GET', '/storage/v1/bucket', 'A-buckets', bearer=A_TOKEN)
# 12. sr bucket 列表
call('GET', '/storage/v1/bucket', 'sr-buckets', apikey=SR_KEY)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb73_storage.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
