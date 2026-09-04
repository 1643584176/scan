# -*- coding: utf-8 -*-
"""外部直连:1) B 真实连接串 2) dbname 变体(postgres 库面)3) B 修正基线"""
import psycopg, http.client, ssl, gzip, json, re, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B, TOKEN_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

A_EP = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
B_EP = 'ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com'
ctx = ssl.create_default_context()


def api(token, site):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    conn.request('GET', '/api/v1/sites/%s/database' % site, headers=h)
    r = conn.getresponse()
    raw = r.read()
    if r.getheader('Content-Encoding') == 'gzip':
        raw = gzip.decompress(raw)
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return out


print('== B 当前连接串 ==')
out = api(TOKEN_B, SITE_B)
print(out[:500])
m = re.search(r'postgresql://([^:]+):([^@]+)@([^/]+)/(\w+)', out)
b_user, b_pwd, b_host, b_db = (m.group(1), m.group(2), m.group(3), m.group(4)) if m else (None,)*4
print('B: user=%s pwd=%s host=%s db=%s' % (b_user, b_pwd and b_pwd[:10] + '...', b_host, b_db))


def try_conn(label, host, user, pwd, db='netlifydb', timeout=10):
    try:
        c = psycopg.connect(host=host, port=5432, user=user, password=pwd, dbname=db,
                            connect_timeout=timeout, sslmode='require')
        with c.cursor() as cur:
            cur.execute('select current_user, current_database(), current_setting(%s)',
                        ('search_path',))
            row = cur.fetchone()
            print('%-36s OK  %s | db=%s | sp=%s' % (label, row[0], row[1], row[2]))
        c.close()
    except Exception as e:
        print('%-36s FAIL %s' % (label, str(e).strip()[:150]))


print()
print('== dbname 变体(A owner × A EP)==')
try_conn('dbname=netlifydb(基线)', A_EP, 'netlifydb_owner', 'npg_MtTpnyk2LE4j')
try_conn('dbname=postgres', A_EP, 'netlifydb_owner', 'npg_MtTpnyk2LE4j', 'postgres')
try_conn('dbname=template1', A_EP, 'netlifydb_owner', 'npg_MtTpnyk2LE4j', 'template1')
try_conn('dbname=不存在', A_EP, 'netlifydb_owner', 'npg_MtTpnyk2LE4j', 'nosuchdb')
try_conn('readonly dbname=postgres', A_EP, 'netlifydb_readonly', 'WCtJ-h-b7w82YMIaM598M75SV7uYVTCv', 'postgres')

print()
print('== B 修正基线 ==')
if b_pwd:
    try_conn('B owner x B EP(API 密码)', b_host, b_user, b_pwd)
    # B 密码在 A 的库上(跨租户对照)
    try_conn('B pwd x A EP(对照)', A_EP, b_user, b_pwd)
