# -*- coding: utf-8 -*-
"""1. projects/count 矛盾排查(org_id 参数)
2. 完整保存 feature_flags 两组 + limits + consumption
3. flag 里找 lakebase/databricks/provisioned 相关
"""
import http.client, ssl, re, os, sys, json, time

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)

def req(path, csrf=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = csrf
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, 'EXC %s' % e

O = 'org-calm-sound-68506202'
print('=== projects 排查 ===', flush=True)
for p in ['/api/v2/projects?org_id=%s' % O,
          '/api/v2/projects/count?org_id=%s' % O,
          '/api/v2/projects/count?organization_id=%s' % O,
          '/api/v2/branches/count?org_id=%s' % O]:
    st, b = req(p, CSRF)
    print('%-75s %s %s' % (p, st, b[:500]), flush=True)
    time.sleep(0.25)

print('=== 保存完整 JSON ===', flush=True)
for name, p in [('_p81_flags_user.json', '/api/v2/users/me/feature_flags'),
                ('_p81_flags_org.json', '/api/v2/organizations/%s/feature_flags' % O),
                ('_p81_limits.json', '/api/v2/organizations/%s/limits' % O),
                ('_p81_consumption.json', '/api/v2/organizations/%s/consumption' % O),
                ('_p81_deletion.json', '/api/v2/organizations/%s/deletion_checklist' % O)]:
    st, b = req(p, CSRF)
    fn = os.path.join(here, name)
    open(fn, 'w', encoding='utf-8').write(b)
    print(fn.split(os.sep)[-1], st, len(b), flush=True)
    time.sleep(0.25)

print('=== flag 关键词扫描 ===', flush=True)
for fn in ['_p81_flags_user.json', '_p81_flags_org.json']:
    try:
        d = json.load(open(os.path.join(here, fn), encoding='utf-8'))
        kws = ['lake', 'databricks', 'provision', 'instance', 'observ', 'agent', 'ai', 'gateway',
               'billing', 'credit', 'addon', 'add-on', 'beta', 'preview', 'internal', 'neon_']
        out = []
        for k, v in d.items():
            if any(w in k.lower() for w in kws):
                out.append('%s=%s' % (k, json.dumps(v)[:90]))
        print(fn, 'total', len(d), 'match', len(out), flush=True)
        print(' | '.join(out)[:3000], flush=True)
    except Exception as e:
        print(fn, 'ERR', e, flush=True)
