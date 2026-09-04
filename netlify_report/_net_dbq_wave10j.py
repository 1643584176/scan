# -*- coding: utf-8 -*-
"""BASE_BACKUP 全量接收(不截断)+ 本地 tar 解析提取关键文件"""
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
        time.sleep(0.01)


pg.send_query(b"BASE_BACKUP")
buf = b''
for i in range(5):
    pump()
    res = pg.get_result()
    if res is None:
        break
    st = res.status
    if st == 12:
        print('FATAL:', res.error_message)
        break
    if st in (3, 5):
        t0 = time.time()
        while time.time() - t0 < 300:
            pump()
            nbytes, data = pg.get_copy_data(1)
            if nbytes > 0:
                buf += data
            elif nbytes == 0:
                time.sleep(0.01)
            else:
                break
        print('stream end: %d bytes in %.1fs' % (len(buf), time.time() - t0))
        break
c.close()

with open(r'D:\scan\netlify_report\_bb_full.bin', 'wb') as f:
    f.write(buf)
print('saved _bb_full.bin', len(buf))

# tar 解析:找 ustar 魔数定位头
import os
names = []
pos = 0
files = {}
limit = len(buf)
while pos + 512 <= limit:
    # 从头解析:tar 头在 pos
    hdr = buf[pos:pos + 512]
    if hdr[257:262] != b'ustar':
        # 错位恢复:搜索下一个 ustar
        nxt = buf.find(b'ustar', pos + 1, pos + 2048)
        if nxt == -1:
            break
        pos = nxt - 257
        continue
    name = hdr[:100].split(b'\0')[0].decode('utf-8', 'replace').rstrip('/')
    try:
        size = int(hdr[124:136].strip(b'\0 ').decode() or b'0', 8)
    except Exception:
        size = 0
    names.append((name, size))
    files[name] = buf[pos + 512:pos + 512 + size]
    pos += 512 + ((size + 511) // 512) * 512
    if len(names) > 500:
        break

print('TOTAL FILES:', len(names))
for n, s in names:
    print('  %10d  %s' % (s, n))

outdir = r'D:\scan\netlify_report\_bb_files'
os.makedirs(outdir, exist_ok=True)
for n, content in files.items():
    p = os.path.join(outdir, n.replace('/', '__'))
    with open(p, 'wb') as f:
        f.write(content)
print('extracted to', outdir)
