# -*- coding: utf-8 -*-
"""T1a: schema 导出全量拉取 (neondb vs postgres) 存文件对比平台对象泄露 (2 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
BID = 'br-wandering-field-w2ob6mpn'
ctx = ssl.create_default_context()

def req(tag, path):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('GET', API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

outdir = os.path.dirname(os.path.abspath(__file__))
for db in ['neondb', 'postgres', 'template1']:
    st, raw = req('schema ' + db, '/projects/%s/branches/%s/schema?db_name=%s' % (PA, BID, db))
    if st == 200:
        d = json.loads(raw)
        sql = d.get('sql', '')
        fn = os.path.join(outdir, '_nz44_schema_%s.sql' % db)
        open(fn, 'w', encoding='utf-8').write(sql)
        print('== %s: %d B SQL 已存 %s' % (db, len(sql), fn))
        # 关键对象摘要
        import re
        objs = re.findall(r'^CREATE (?:TABLE|VIEW|FUNCTION|TRIGGER|SEQUENCE|SCHEMA|EXTENSION|TYPE|RULE|EVENT TRIGGER)[^;]*', sql, re.M)
        print('   objects: %d' % len(objs))
        for o in objs[:60]:
            print('   | ' + o.replace('\n', ' ')[:150])
    else:
        print('== %s -> %d %s' % (db, st, raw[:200]))
