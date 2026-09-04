# -*- coding: utf-8 -*-
"""pg_cron schema 侦察 + lakebase/vector 安装链(postgres 库 & netlifydb 库)"""
import psycopg, http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

A_EP = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
ctx = ssl.create_default_context()

# ---- 外部直连(postgres 库)----
conn = psycopg.connect(host=A_EP, port=5432, user='netlifydb_owner',
                       password='npg_MtTpnyk2LE4j', dbname='postgres',
                       connect_timeout=10, sslmode='require', autocommit=True)


def show(label, sql, n=30):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        print('==== %s (%d rows) cols=%s ====' % (label, len(rows), cols))
        for r in rows[:n]:
            print(' ', str(r)[:300])
    except Exception as e:
        print('==== %s ERR %s ====' % (label, str(e).strip()[:220]))
    print()


print('######## postgres 库:cron/timescale schema ########')
show('cron schema 存在?', "select n.nspname from pg_namespace n where n.nspname in ('cron','timescaledb','_timescaledb_cache','_timescaledb_catalog','_timescaledb_config','_timescaledb_internal','lakebase')")
show('所有 schema', "select nspname, nspowner::regrole from pg_namespace where nspname not like 'pg\\_%' and nspname<>'information_schema' order by 1")
show('cron 函数', "select p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' from pg_proc p "
     "join pg_namespace n on p.pronamespace=n.oid where n.nspname='cron' order by 1")
show('cron job 表', "select c.relname from pg_class c join pg_namespace n on c.relnamespace=n.oid where n.nspname='cron'")
show('lakebase 函数', "select p.proname||'('||pg_get_function_identity_arguments(p.oid)||')', p.prosecdef from pg_proc p "
     "join pg_namespace n on p.pronamespace=n.oid where n.nspname='public' and p.proname like 'lakebase%' or "
     "(p.proname like '%embed%' or p.proname like '%rag%') order by 1")
conn.close()

print()
print('######## netlifydb 库(vector/lakebase 安装链)########')


def dq(sql):
    conn2 = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn2.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn2.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:1000].decode('utf-8', 'ignore')
    conn2.close()
    return st, out


st, out = dq("select name, default_version from pg_available_extensions where name in ('vector','lakebase_vector','lakebase_text','lakebase_tokenizer','timescaledb','pg_partman','rag_bge_small_en_v15','rag_jina_reranker_v1_tiny_en')")
print('可用性 [%d] %s' % (st, out[:900]))
for ext in ['vector', 'lakebase_vector', 'lakebase_text']:
    st, out = dq('create extension if not exists "%s"' % ext)
    print('create %-18s [%d] %s' % (ext, st, out[:250]))
st, out = dq("select extname from pg_extension order by 1")
print('exts now [%d] %s' % (st, out[:400]))
