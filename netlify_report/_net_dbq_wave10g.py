# -*- coding: utf-8 -*-
"""BASE_BACKUP 标准 libpq 泵:get_result -> COPY 状态 -> get_copy_data"""
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


def pump():
    while True:
        pg.consume_input()
        if not pg.is_busy():
            return
        time.sleep(0.02)


def next_result():
    pump()
    return pg.get_result()


pg.send_query(b"BASE_BACKUP")
# 第一步:取结果直到出现 COPY 或错误
buf = b''
res = None
while True:
    res = next_result()
    if res is None:
        print('no more results, got %d bytes' % len(buf))
        break
    st = res.status
    print('result status:', st, 'error:', res.error_message if st == 3 else '')
    if st == 3:  # FATAL_ERROR
        break
    if st in (4, 5, 6):  # COPY_IN/OUT/BOTH(psycopg enum)
        t0 = time.time()
        while time.time() - t0 < 120:
            pump()
            nbytes, data = pg.get_copy_data(1)
            if nbytes > 0:
                buf += data
                if len(buf) > 262144:
                    break
            elif nbytes == 0:
                time.sleep(0.02)
            else:
                break
        print('copy phase done, total %d bytes' % len(buf))
        break

print('final buf len:', len(buf))
if buf:
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
            if len(names) >= 30:
                break
        else:
            print('non-tar at pos', pos)
            break
    print('FILES:', names)
    with open(r'D:\scan\netlify_report\_bb_head.bin', 'wb') as f:
        f.write(buf)
    print('saved _bb_head.bin')
# 收尾
try:
    while True:
        r2 = next_result()
        if r2 is None:
            break
        print('tail status:', r2.status)
except Exception as e:
    print('tail ERR:', str(e)[:150])
c.close()
