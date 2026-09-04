# -*- coding: utf-8 -*-
"""公开侦察7: 从页面 stub 收集依赖 chunk -> 分批下载 -> grep 端点
聚焦页面: sql / extensions / roles / api-keys / column-privileges / replication / jwt / settings
"""
import re, os, http.client, ssl, glob

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
jsdir = os.path.join(here, '_sb_js')
ASSET = 'frontend-assets.supabase.com'
BASE = '/studio/e25c0e83dff6/_next/'

# 1. 收集依赖
deps = set()
for fn in glob.glob(os.path.join(jsdir, '*.js')):
    src = open(fn, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'"static/chunks/([^"]+\.js)"', src):
        deps.add('static/chunks/' + m.group(1))
print('total deps:', len(deps), flush=True)

# 2. 下载(跳过已有), 每批 grep
def dl_and_grep(cs):
    found = {}
    for c in sorted(cs):
        name = c.split('/')[-1]
        fp = os.path.join(jsdir, name)
        if not (os.path.exists(fp) and os.path.getsize(fp) > 1000):
            try:
                conn = http.client.HTTPSConnection(ASSET, context=ctx, timeout=30)
                conn.request('GET', BASE + c, headers={'User-Agent': 'Mozilla/5.0'})
                r = conn.getresponse()
                raw = r.read()
                conn.close()
                if r.status == 200:
                    open(fp, 'wb').write(raw)
                else:
                    continue
            except Exception:
                continue
        try:
            src = open(fp, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if 'pg-meta' in src or 'pg_meta' in src:
            found[name] = len(src)
    return found

done = set()
for i in range(12):
    todo = deps - done
    if not todo:
        break
    batch = sorted(todo)[:120]
    done |= set(batch)
    found = dl_and_grep(batch)
    print('batch %d: dl %d, pg-meta hits: %s' % (i, len(batch), list(found)), flush=True)
    if found:
        break
print('done total downloaded:', len([f for f in glob.glob(os.path.join(jsdir, '*.js'))]), flush=True)
