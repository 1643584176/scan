# -*- coding: utf-8 -*-
"""BASE_BACKUP 修正版:COPY_OUT(3)/COPY_BOTH(5) 进入 copy 读,读满即断
libpq 枚举:0 EMPTY 1 OK 2 TUPLES 3 COPY_OUT 4 COPY_IN 5 COPY_BOTH 6 SINGLE 12 FATAL
"""
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

MAX = 524288  # 只读 512KB 看文件清单,然后断开


def pump():
    while True:
        pg.consume_input()
        if not pg.is_busy():
            return
        time.sleep(0.01)


pg.send_query(b"BASE_BACKUP")
pump()
res = pg.get_result()
st = res.status if res else -1
print('first result status:', st)
if res is not None and st == 12:
    print('FATAL:', res.error_message)
    c.close()
    sys.exit(1)

buf = b''
t0 = time.time()
if st in (3, 5):  # COPY_OUT / COPY_BOTH
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
    print('copy done, got %d bytes in %.1fs' % (len(buf), time.time() - t0))

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
            print('non-tar at pos %d, hdr=%r' % (pos, hdr[:16]))
            break
    print('FILES(%d):' % len(names), names)
    with open(r'D:\scan\netlify_report\_bb_head.bin', 'wb') as f:
        f.write(buf)
    print('saved _bb_head.bin %d bytes' % len(buf))
else:
    print('no data; tail status:', res.status if res else None)
c.close()
print('done')
