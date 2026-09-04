# -*- coding: utf-8 -*-
"""DB 细测 D: vault 0.3.1 写读删机制 + auth 表全清单 + realtime 对象 + pg_cron 边界"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def q(sql, tag, maxb=30000):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:18000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. vault 表结构 (0.3.1: key_id? 加密列?)
q("select column_name, data_type from information_schema.columns where table_schema='vault' order by table_name, ordinal_position;", "vault-cols")
# 2. create_secret 写入探测 (可逆: 随后删除)
q("select vault.create_secret('sbx_probe_val_9x7k', 'sbx_probe_name_9x7k') sid;", "vault-write")
# 3. 解密视图可见性 (含 key 列形态)
q("select name, decrypted_secret, key_id from vault.decrypted_secrets where name='sbx_probe_name_9x7k';", "vault-dec")
# 4. 原始行 + 清理
q("delete from vault.secrets where name='sbx_probe_name_9x7k' returning name, secret is null as secret_null, key_id;", "vault-clean")
# 5. auth 表全清单 (GoTrue 2026 结构情报)
q("select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='auth' and c.relkind='r' order by 1;", "auth-tables")
# 6. realtime 对象清单
q("select c.relname, c.relkind from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='realtime' and c.relkind in ('r','v','m') order by 1;", "rt-tables")
# 7. pg_cron 扩展创建边界
q("create extension if not exists pg_cron;", "ext-pgcron")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb41_vault.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9000])
