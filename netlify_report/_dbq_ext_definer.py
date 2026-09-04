# -*- coding: utf-8 -*-
"""① 扩展 definer 全量枚举(只读):已装扩展中 SECURITY DEFINER 函数 + owner
若存在 owner=cloud_admin 且租户可 execute 的 definer -> 同 pg_repack 模式(记录不提交)
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def q(sql, trunc=4000):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=45)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:trunc].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


sql = """
select e.extname, n.nspname, p.proname,
       p.proowner::regrole::text as owner,
       pg_get_function_identity_arguments(p.oid) as args,
       p.provolatile
from pg_extension e
join pg_depend d on d.refobjid = e.oid and d.deptype = 'e'
join pg_proc p on p.oid = d.objid
join pg_namespace n on n.oid = p.pronamespace
where p.prosecdef
order by e.extname, p.proname
"""
st, out = q(sql)
print('== 扩展内 SECURITY DEFINER 函数 ==')
print('[%d]' % st)
print(out[:4000])
print()

sql2 = """
select e.extname, count(*) as total_funcs,
       count(*) filter (where p.prosecdef) as definer_funcs,
       count(*) filter (where p.proowner::regrole::text <> 'netlifydb_owner') as non_owner_funcs
from pg_extension e
join pg_depend d on d.refobjid = e.oid and d.deptype = 'e'
join pg_proc p on p.oid = d.objid
group by e.extname order by e.extname
"""
st, out = q(sql2)
print('== 扩展函数统计(owner 分布)==')
print('[%d]' % st)
print(out[:2000])
print()

sql3 = """
select e.extname, count(*) as triggers
from pg_extension e
join pg_depend d on d.refobjid = e.oid and d.deptype = 'e'
join pg_trigger t on t.oid = d.objid
group by e.extname
union all
select 'EVENT', count(*) from pg_event_trigger
"""
st, out = q(sql3)
print('== 扩展触发器/事件触发器 ==')
print('[%d]' % st)
print(out[:1500])
