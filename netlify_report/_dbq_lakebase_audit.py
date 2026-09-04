# -*- coding: utf-8 -*-
"""lakebase/vector 扩展函数审计(definer/权限/文件/模型路径参数)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def q(sql, trunc=3000):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:trunc].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def show(label, sql, trunc=3000):
    st, out = q(sql, trunc)
    print('==== %s [%d] ====' % (label, st))
    print(out[:trunc])
    print()


show('lakebase 全部函数', "select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' as fn, "
     "r.rolname as owner, p.prosecdef, p.provolatile, p.proparallel, "
     "coalesce(p.proacl::text,'(default)') as acl "
     "from pg_proc p join pg_namespace n on p.pronamespace=n.oid join pg_roles r on p.proowner=r.oid "
     "where p.proname like 'lakebase%' or p.proname like '%embed%' or p.proname like '%rag%' "
     "or p.proname like '%tokenizer%' or p.proname like '%rerank%' order by 1", 4000)

show('vector 函数', "select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' as fn, "
     "r.rolname as owner, p.prosecdef from pg_proc p join pg_namespace n on p.pronamespace=n.oid "
     "join pg_roles r on p.proowner=r.oid where n.nspname='public' and p.proname in "
     "('vector','array_to_vector','vector_to_float4','l2_distance','cosine_distance','inner_product','binary_quantize') "
     "order by 1", 2500)

show('lakebase 类型/表', "select c.relname, c.relkind, r.rolname from pg_class c join pg_namespace n on c.relnamespace=n.oid "
     "join pg_roles r on c.relowner=r.oid where n.nspname='public' and "
     "(c.relname like 'lakebase%' or c.relname like '%rag%') order by 1", 1500)

show('lakebase 扩展依赖', "select e.extname, d.refobjid::regclass::text from pg_depend d "
     "join pg_extension e on d.refobjid=e.oid where d.classid='pg_class'::regclass and e.extname like 'lakebase%' "
     "order by 1", 1500)

show('models 相关', "select name, setting from pg_settings where name like '%model%' or name like '%rag%' or name like '%lakebase%' or name like '%embed%'", 2000)
