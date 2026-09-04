# -*- coding: utf-8 -*-
"""staging 测试资产 setup:项目/DataAPI/Bucket/Credential(温和节奏,≤10rps)"""
import http.client, ssl, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

def csrf_token():
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf='):
            return urllib.parse.unquote(c.split('=', 1)[1])
    return None

def api(method, path, body=None, extra_hdr=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': cookie_str()}
    h.update(HEADERS_TEST)
    tok = csrf_token()
    if tok:
        h['X-CSRF-Token'] = tok
    if extra_hdr:
        h.update(extra_hdr)
    data = json.dumps(body).encode() if body is not None else None
    conn.request(method, API_BASE + path, body=data, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

def show(tag, st, raw):
    print('\n== %s -> %d' % (tag, st))
    try:
        print(json.dumps(json.loads(raw), indent=1, ensure_ascii=False)[:900])
    except Exception:
        print(raw[:300])
    return raw

# 1. 建项目
st, raw = api('POST', '/projects?org_id=%s' % ORG, {'project': {'name': 'sec-pccp-1'}})
show('POST /projects', st, raw)
try:
    pid = json.loads(raw)['project']['id']
except Exception:
    print('FAILED create project'); sys.exit(1)
time.sleep(1)

# 2. 分支列表(默认 main 应已存在)
st, raw = api('GET', '/projects/%s/branches' % pid)
show('GET branches', st, raw)
branches = json.loads(raw).get('branches', [])
bid = branches[0]['id'] if branches else None
print('\nproject=%s branch=%s' % (pid, bid))
time.sleep(1)

if bid:
    # 3. Data API(空配置看默认)
    st, raw = api('POST', '/projects/%s/branches/%s/data-api/neondb' % (pid, bid), {})
    show('POST data-api/neondb', st, raw)
    time.sleep(1)

    # 4. Bucket
    st, raw = api('POST', '/projects/%s/branches/%s/buckets' % (pid, bid), {'name': 't1', 'access_level': 'private'})
    show('POST buckets t1', st, raw)
    time.sleep(1)

    # 5. Credential(storage:read)
    st, raw = api('POST', '/projects/%s/branches/%s/credentials' % (pid, bid),
                  {'name': 'cred1', 'scopes': ['storage:read'], 'principal_type': 'user'})
    show('POST credentials', st, raw)

print('\nDONE pid=%s bid=%s' % (pid, bid))
