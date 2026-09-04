# -*- coding: utf-8 -*-
"""清理: 删除 bucket 内对象 -> 删 bucket"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
out = []
def call(method, path, body=None, tag='', maxb=6000, retries=2):
    body_j = json.dumps(body) if body is not None else None
    for i in range(retries):
        c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
        h = {"User-Agent": UA, "Accept": "application/json", "apikey": SR_KEY,
             "Authorization": "Bearer " + SR_KEY}
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

# 1. 删对象 (逐个)
call('DELETE', '/storage/v1/object/sbx_priv/sr_file.txt', None, 'del-obj-priv')
call('DELETE', '/storage/v1/object/sbx_pub/pub_file.txt', None, 'del-obj-pub')
# 2. 再删 bucket
call('DELETE', '/storage/v1/bucket/sbx_priv?emptiedBucket=true', None, 'del-bucket-priv')
call('DELETE', '/storage/v1/bucket/sbx_pub?emptiedBucket=true', None, 'del-bucket-pub')
# 3. 确认
call('GET', '/storage/v1/bucket', 'buckets-final')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb75_bucketclean.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
