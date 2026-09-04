# -*- coding: utf-8 -*-
"""T1 schema导出跨库 + T2 permissions/backup_schedule/shared 只读探测 (9 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
BID = 'br-wandering-field-w2ob6mpn'  # A main
ctx = ssl.create_default_context()

def req(tag, path):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('GET', API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-34s -> %d' % (tag, r.status))
            print('   %s' % raw[:450].decode('utf-8', 'replace').replace('\n', ' '))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

req('schema db=neondb', '/projects/%s/branches/%s/schema?db_name=neondb' % (PA, BID))
req('schema db=postgres(平台库!)', '/projects/%s/branches/%s/schema?db_name=postgres' % (PA, BID))
req('schema db=template1', '/projects/%s/branches/%s/schema?db_name=template1' % (PA, BID))
req('schema db=不存在', '/projects/%s/branches/%s/schema?db_name=nonexist_zz' % (PA, BID))
req('compare_schema base=main', '/projects/%s/branches/%s/compare_schema?db_name=neondb&base_branch_id=%s' % (PA, BID, BID))
req('permissions 列表', '/projects/%s/permissions' % PA)
req('shared 项目', '/projects/shared')
req('backup_schedule', '/projects/%s/branches/%s/backup_schedule' % (PA, BID))
req('A 分支列表', '/projects/%s/branches' % PA)
