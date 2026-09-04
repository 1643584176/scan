# -*- coding: utf-8 -*-
"""BASE_BACKUP via psycopg3 copy():读数据目录流(分段,只看头部文件)
"""
import sys, re, json, http.client, ssl
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
PW, HOST, DB = m.group(1), m.group(2), m.group(3)

import psycopg
c = psycopg.connect(host=HOST, port=5432, dbname=DB, user='netlifydb_owner', password=PW,
                    sslmode='require', connect_timeout=10, replication='database', autocommit=True)
try:
    with c.cursor() as cur:
        with cur.copy("BASE_BACKUP LABEL 'probe_bb'") as copy:
            # tar 流:读前 200KB 找文件名头(512 字节对齐 tar header)
            buf = b''
            while len(buf) < 262144:
                chunk = copy.read(65536)
                if not chunk:
                    break
                buf += chunk
            # 解析 tar 文件名(从 backup_label 或第一个文件开始)
            names = []
            pos = 0
            while pos + 512 <= len(buf):
                hdr = buf[pos:pos + 512]
                name = hdr[:100].split(b'\0')[0].decode('utf-8', 'replace')
                if name and hdr[257:262] == b'ustar':
                    names.append(name)
                    size = int(hdr[124:136].strip(b'\0 ').decode() or b'0', 8)
                    pos += 512 + ((size + 511) // 512) * 512
                    if len(names) >= 20:
                        break
                else:
                    break
            print('FILES:', names)
            print('BUF_HEAD:', buf[:300])
            # 保存前 256KB 供本地分析
            with open(r'D:\scan\netlify_report\_bb_head.bin', 'wb') as f:
                f.write(buf)
            print('saved _bb_head.bin', len(buf))
except Exception as e:
    print('BASE_BACKUP ERR:', str(e)[:400])
c.close()
