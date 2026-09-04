# -*- coding: utf-8 -*-
"""公开侦察5: 解析 manifest -> 下载攻击面页面 chunk 到 _sb_js/
路由目标: sql/database 各页/settings api-keys,jwt,infrastructure/addons/functions
"""
import re, os, http.client, ssl

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(here, '_sb_js'), exist_ok=True)
ASSET = 'frontend-assets.supabase.com'
BASE = '/studio/e25c0e83dff6/_next/'

txt = open(os.path.join(here, '_sb05_buildManifest.js'), encoding='utf-8', errors='replace').read()

# route: [chunks]
route_chunks = {}
for mm in re.finditer(r'^\s*"([^"]+)":\s*\[(.*?)\]\s*,?\s*$', txt, re.M | re.S):
    route = mm.group(1)
    chunks = re.findall(r'"([^"]+)"', mm.group(2))
    route_chunks[route] = chunks
print('routes total:', len(route_chunks), flush=True)

WANT = ['/project/[ref]/sql', '/project/[ref]/sql/[id]', '/project/[ref]/sql/templates',
        '/project/[ref]/database/extensions', '/project/[ref]/database/roles',
        '/project/[ref]/database/functions', '/project/[ref]/database/settings',
        '/project/[ref]/database/column-privileges', '/project/[ref]/database/publications',
        '/project/[ref]/database/replication', '/project/[ref]/database/replication/[pipelineId]',
        '/project/[ref]/settings/api-keys', '/project/[ref]/settings/jwt',
        '/project/[ref]/settings/addons', '/project/[ref]/settings/infrastructure',
        '/project/[ref]/functions', '/project/[ref]/functions/[functionSlug]/secrets'.replace('/secrets', ''),
        '/project/[ref]/settings/webhooks', '/project/[ref]/database/tables', '/project/[ref]/database/policies',
        '/project/[ref]/storage/files', '/project/[ref]/database/backups/pitr',
        '/project/[ref]/database/backups/scheduled', '/project/[ref]/database/migrations',
        '/project/[ref]/database/triggers', '/project/[ref]/observability/database',
        ]
have = {}
for rt in WANT:
    if rt in route_chunks:
        for c in route_chunks[rt]:
            have[c] = have.get(c, 0) + 1
            print('WANT %s -> %s' % (rt, c), flush=True)
    else:
        print('WANT MISSING:', rt, flush=True)

# 共享 chunk(所有路由公共的也要: "static/chunks/xxx.js" 在 head?) 先下载目标
print('unique chunks to dl:', len(have), flush=True)
ok = 0
for c in sorted(have):
    fn = os.path.join(here, '_sb_js', c.split('/')[-1])
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        ok += 1
        continue
    try:
        conn = http.client.HTTPSConnection(ASSET, context=ctx, timeout=30)
        conn.request('GET', BASE + c, headers={'User-Agent': 'Mozilla/5.0'})
        r = conn.getresponse()
        raw = r.read()
        conn.close()
        if r.status == 200:
            open(fn, 'wb').write(raw)
            ok += 1
        else:
            print('DL FAIL', c, r.status, flush=True)
    except Exception as e:
        print('DL EXC', c, e, flush=True)
print('downloaded ok:', ok, flush=True)
