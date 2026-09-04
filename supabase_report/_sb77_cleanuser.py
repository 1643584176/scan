# -*- coding: utf-8 -*-
"""清理 invite 测试用户 cdd6a98a (sr admin API)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
def call(method, path, tag=''):
    c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "apikey": SR_KEY,
         "Authorization": "Bearer " + SR_KEY}
    h.update(VDP_HEADERS)
    try:
        c.request(method, path, headers=h)
        r = c.getresponse()
        b = r.read(3000).decode('utf-8', errors='replace')
        print('[%s] %s | %s' % (tag, r.status, b[:500]))
        c.close()
    except Exception as e:
        print('[%s] ERR %s' % (tag, e))

call('DELETE', '/auth/v1/admin/users/cdd6a98a-6165-4641-9e7e-d0e3e4a6b281', 'del-invite-user')
call('GET', '/auth/v1/admin/users?per_page=10', 'user-list')
