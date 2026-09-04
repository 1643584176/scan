# -*- coding: utf-8 -*-
"""紧急: 建 RLS 测试表 + 注册用户 B + 保存 tokens (mgmt token 快过期)"""
import http.client, ssl, json, time, os, sys, random, string, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
AUTH_HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', host=API_HOST, headers_extra=None, maxb=6000):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(host, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers_extra:
        h.update(headers_extra)
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

def q(sql, tag):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s]\n%s | %s' % (tag, r.status, b[:2000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))
        return 0, str(e)

# 1. 建 RLS 测试表 (owner=postgres, RLS on, uid 行隔离)
DDL = """
create table if not exists public.sbx_rls_t (
  id bigint generated always as identity primary key,
  owner uuid not null default auth.uid(),
  secret text not null,
  created_at timestamptz default now()
);
alter table public.sbx_rls_t enable row level security;
drop policy if exists sbx_rls_sel on public.sbx_rls_t;
create policy sbx_rls_sel on public.sbx_rls_t for select using (owner = auth.uid());
drop policy if exists sbx_rls_ins on public.sbx_rls_t;
create policy sbx_rls_ins on public.sbx_rls_t for insert with check (owner = auth.uid());
drop policy if exists sbx_rls_upd on public.sbx_rls_t;
create policy sbx_rls_upd on public.sbx_rls_t for update using (owner = auth.uid());
grant select, insert, update on public.sbx_rls_t to authenticated;
grant usage on sequence public.sbx_rls_t_id_seq to authenticated;
"""
q(DDL, 'mk-rls-tbl')
# 2. 注册用户 B
suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
B_EMAIL = 'sbx_b%s@qq.com' % suffix
B_PASS = 'Sbxtest123!'
print('B_EMAIL=%s' % B_EMAIL)
st, b = req('POST', '/auth/v1/signup', {"email": B_EMAIL, "password": B_PASS}, 'signup-B',
            host=AUTH_HOST, headers_extra={"apikey": ANON_KEY})
m = re.search(r'"id":"([0-9a-f-]{36})"', b)
B_ID = m.group(1) if m else ''
q("update auth.users set email_confirmed_at=now() where email='%s' returning id;" % B_EMAIL, 'confirm-B')
# 3. 用户 B password grant
st2, b2 = req('POST', '/auth/v1/token?grant_type=password', {"email": B_EMAIL, "password": B_PASS},
              'grant-B', host=AUTH_HOST, headers_extra={"apikey": ANON_KEY})
m2 = re.search(r'"access_token":"([^"]+)"', b2)
B_TOKEN = m2.group(1) if m2 else ''
# 4. 保存 B token
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'w').write(json.dumps({
    'B_EMAIL': B_EMAIL, 'B_PASS': B_PASS, 'B_ID': B_ID, 'B_TOKEN': B_TOKEN
}))
print('B_ID=%s' % B_ID)
print('B_TOKEN_LEN=%d' % len(B_TOKEN))

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb66_prep.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
