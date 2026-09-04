# -*- coding: utf-8 -*-
"""带 org_id 查项目列表 + 交叉验证 presign 是否全局挂"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ORG = 'org-flat-dawn-91601224'

def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

st, raw = req('GET', '/projects?org_id=%s' % ORG)
print('projects -> %d | %s' % (st, raw.decode(errors='replace')[:800]))
try:
    projects = json.loads(raw).get('projects', [])
except Exception:
    projects = []

for prj in projects:
    pid = prj['id']
    st2, raw2 = req('GET', '/projects/%s/branches' % pid)
    branches = json.loads(raw2).get('branches', []) if st2 == 200 else []
    primary = next((b for b in branches if b.get('primary')), branches[0] if branches else None)
    if not primary:
        print('project %s: no branch' % pid); continue
    bid = primary['id']
    print('=== project %s branch %s' % (pid, bid))
    st3, raw3 = req('POST', '/projects/%s/branches/%s/buckets' % (pid, bid), {'name': 'kx1'})
    print('  create kx1 -> %d | %s' % (st3, raw3.decode(errors='replace')[:150]))
    if st3 in (200, 201):
        st4, raw4 = req('POST', '%s/projects/%s/branches/%s/buckets/kx1/objects/o1.txt/presign' % (API_BASE, pid, bid),
                        {'operation': 'upload', 'content_type': 'text/plain'})
        print('  presign kx1 -> %d | %s' % (st4, raw4.decode(errors='replace')[:150]))
        req('DELETE', '/projects/%s/branches/%s/buckets/kx1' % (pid, bid))
        print('  deleted kx1')
    else:
        print('  create failed (maybe exists)')
