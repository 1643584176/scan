# -*- coding: utf-8 -*-
"""BASE_BACKUP v3:循环 get_result 直到 COPY_OUT/COPY_BOTH,再读 copy"""
import sys, re, json, time, http.client, ssl
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
conn.request('GET', '/api/v1/sites/%s/database' % SITE_ID, headers={'Authorization': AUTH_HEADER, 'Accept': 'application/json'})
r = conn.getresponse()
d = json.loads(r.read().decode('utf-8', 'replace'))
conn.close()
cs = d.get('connection_strings', {}).get('netlifydb_owner', '')
m = re.search(r'postgresql://netlifydb_owner:([^@]+)@([^/]+)/(\w+)', cs)

import psycopg
c = psycopg.connect(host=m.group(2), port=5432, dbname=m.group(3), user='netlifydb_owner', password=m.group(1),
                    sslmode='require', connect_timeout=10, replication='database', autocommit=True)
pg = c.pgconn

MAX = 524288


def pump():
    while True:
        pg.consume_input()
        if not pg.is_busy():
            return
        time.sleep(0.01)


pg.send_query(b"BASE_BACKUP")
# 循环取结果直到 COPY 或错误
buf = b''
got_copy = False
for i in range(5):
    pump()
    res = pg.get_result()
    if res is None:
        print('result %d: None (stream end)' % i)
        break
    st = res.status
    if st == 12:
        print('result %d: FATAL %s' % (i, res.error_message))
        break
    if st == 2:  # TUPLES_OK:打印行内容(诊断)
        try:
            n = res.ntuples
            rows = [res.get_value(0, r) for r in range(n)]
            print('result %d: TUPLES_OK n=%d rows=%r' % (i, n, rows[:3]))
        except Exception as e:
            print('result %d: TUPLES_OK (read err %s)' % (i, str(e)[:100]))
        continue
    if st in (3, 5):  # COPY_OUT / COPY_BOTH
        print('result %d: COPY status=%d, reading stream...' % (i, st))
        got_copy = True
        t0 = time.time()
        while time.time() - t0 < 180:
            pump()
            nbytes, data = pg.get_copy_data(1)
            if nbytes > 0:
                buf += data
                if len(buf) >= MAX:
                    break
            elif nbytes == 0:
                time.sleep(0.01)
            else:
                break
        print('copy done, %d bytes in %.1fs' % (len(buf), time.time() - t0))
        break
    print('result %d: status=%d' % (i, st))

names = []
if buf:
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
            if len(names) >= 40:
                break
        else:
            print('non-tar at pos %d hdr=%r' % (pos, hdr[:16]))
            break
    print('FILES(%d):' % len(names), names)
    with open(r'D:\scan\netlify_report\_bb_head.bin', 'wb') as f:
        f.write(buf)
    print('saved %d bytes' % len(buf))
c.close()
print('done')
