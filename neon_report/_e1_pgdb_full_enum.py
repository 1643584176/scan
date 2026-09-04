# -*- coding: utf-8 -*-
"""全库枚举(纯只读,零破坏):本 compute 所有可连 DB 的 schema/表/列 + 内容抽样 + 敏感词标记
目标:发现 d17-d20 未覆盖的平台表/敏感数据(与 #3992341 主题隔离:不做任何提权/写操作)"""
import psycopg
from urllib.parse import quote

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
USER = 'neondb_owner'
BASE = 'postgresql://%s:%s@%s' % (USER, PWD, HOST)

SENS_COLS = ('token', 'password', 'secret', 'credential', 'jwt', 'jwk', 'private',
             'connstr', 'api_key', 'tenant', 'storage', 'hash', 'sig', 'auth',
             'key', 'url', 'host', 'email', 'phone')
SENS_VALS = ('eyj', 'password', 'secret', '-----begin', 'postgres://', 'npg_',
             'http', 'token', 'bearer', 'access_key', 'private_key')

def esc(v, n=160):
    s = repr(v)
    if len(s) > n:
        return s[:n] + '...(%dB)' % len(s)
    return s

def hit_sens(rec):
    cols = [c[0] for c in rec['cols']]
    hits = []
    for i, cn in enumerate(cols):
        if any(k in cn.lower() for k in SENS_COLS):
            hits.append('COL:%s' % cn)
        for row in rec.get('rows', []):
            try:
                sv = str(row[i]).lower()
            except Exception:
                continue
            if any(k in sv for k in SENS_VALS):
                hits.append('VAL:%s=%s' % (cn, esc(row[i], 60)))
                break
    return sorted(set(hits))

def enum_db(dbname):
    uri = '%s/%s' % (BASE, quote(dbname))
    try:
        conn = psycopg.connect(uri, connect_timeout=15)
    except Exception as e:
        print('## DB %s: CONN ERR: %s' % (dbname, str(e)[:200]))
        return
    conn.autocommit = True
    cur = conn.cursor()
    print('\n########################################')
    print('## DB: %s (connected OK)' % dbname)
    print('########################################')
    # 1. non-system schemas
    cur.execute("""SELECT nspname FROM pg_namespace
                   WHERE nspname NOT LIKE 'pg\\_%' AND nspname <> 'information_schema'
                   ORDER BY 1""")
    schemas = [r[0] for r in cur.fetchall()]
    print('schemas:', schemas)
    for sch in schemas:
        # 2. tables/views/matviews
        cur.execute("""SELECT c.relname, c.relkind, pg_get_userbyid(c.relowner),
                              COALESCE(c.relacl::text,''), c.reltuples::bigint
                       FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                       WHERE n.nspname=%s AND c.relkind IN ('r','v','m','f','p')
                       ORDER BY c.relname""", (sch,))
        rels = cur.fetchall()
        if not rels:
            continue
        print('\n--- schema %s: %d rels ---' % (sch, len(rels)))
        for relname, kind, owner, acl, tuples in rels:
            print('  %-30s kind=%s owner=%-15s rows~%-8s acl=%s' % (relname, kind, owner, tuples, acl[:120]))
            # 3. columns + sample (only tables incl. partitioned)
            if kind in ('r', 'f', 'p'):
                try:
                    cur.execute("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
                                   FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
                                   WHERE c.relname=%s AND c.relnamespace=(SELECT oid FROM pg_namespace WHERE nspname=%s)
                                     AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum""",
                                (relname, sch))
                    cols = cur.fetchall()
                    if not cols:
                        continue
                    print('      cols:', ', '.join('%s %s' % (cn, ty) for cn, ty in cols))
                    nrows = 8 if tuples <= 100 else 4
                    cur.execute(sql_safe_select(sch, relname, cols, nrows))
                    rows = cur.fetchall()
                    if rows:
                        print('      rows:')
                        for r in rows:
                            print('        ', ' | '.join(esc(x, 90) for x in r))
                        rec = {'cols': cols, 'rows': rows}
                        hs = hit_sens(rec)
                        if hs:
                            print('      *** SENSITIVE HITS: %s' % '; '.join(hs))
                except Exception as e:
                    print('      read ERR: %s' % str(e)[:200])
    conn.close()

def sql_safe_select(sch, rel, cols, limit):
    from psycopg import sql as pgsql
    q = pgsql.SQL('SELECT {cols} FROM {tbl} LIMIT {lim}').format(
        cols=pgsql.SQL(',').join(pgsql.Identifier(c) for c, _ in cols),
        tbl=pgsql.Identifier(sch, rel),
        lim=pgsql.Literal(limit))
    return q

if __name__ == '__main__':
    # 0. discover DBs
    uri0 = '%s/postgres' % BASE
    conn = psycopg.connect(uri0, connect_timeout=15)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""SELECT datname FROM pg_database
                   WHERE datallowconn AND datname NOT LIKE 'template%'
                   ORDER BY 1""")
    dbs = [r[0] for r in cur.fetchall()]
    print('discovered DBs:', dbs)
    conn.close()
    for db in dbs:
        enum_db(db)
