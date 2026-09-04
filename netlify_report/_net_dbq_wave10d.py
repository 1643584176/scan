# -*- coding: utf-8 -*-
"""BASE_BACKUP 无 LABEL / LABEL 变体 via copy()"""
import sys, re, json, http.client, ssl
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def fresh_conn():
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    conn.request('GET', '/api/v1/sites/%s/database' % SITE_ID, headers={'Authorization': AUTH_HEADER, 'Accept': 'application/json'})
    r = conn.getresponse()
    d = json.loads(r.read().decode('utf-8', 'replace'))
    conn.close()
    cs = d.get('connection_strings', {}).get('netlifydb_owner', '')
    m = re.search(r'postgresql://netlifydb_owner:([^@]+)@([^/]+)/(\w+)', cs)
    return m.group(1), m.group(2), m.group(3)


import psycopg

for tag, cmd in [("D1", "BASE_BACKUP"), ("D2", "BASE_BACKUP LABEL probe"), ("D3", "BASE_BACKUP NOWAIT")]:
    PW, HOST, DB = fresh_conn()
    c = psycopg.connect(host=HOST, port=5432, dbname=DB, user='netlifydb_owner', password=PW,
                        sslmode='require', connect_timeout=10, replication='database', autocommit=True)
    try:
        with c.cursor() as cur:
            with cur.copy(cmd) as copy:
                buf = copy.read(262144)
                print('%s OK got %d bytes' % (tag, len(buf)))
                names = []
                pos = 0
                while pos + 512 <= len(buf):
                    hdr = buf[pos:pos + 512]
                    name = hdr[:100].split(b'\0')[0].decode('utf-8', 'replace')
                    if name and hdr[257:262] == b'ustar':
                        names.append(name)
                        try:
                            size = int(hdr[124:136].strip(b'\0 ').decode() or b'0', 8)
                        except Exception:
                            size = 0
                        pos += 512 + ((size + 511) // 512) * 512
                        if len(names) >= 15:
                            break
                    else:
                        break
                print('   FILES:', names)
                with open(r'D:\scan\netlify_report\_bb_head.bin', 'wb') as f:
                    f.write(buf)
    except Exception as e:
        print('%s ERR: %s' % (tag, str(e)[:300]))
    c.close()
