# -*- coding: utf-8 -*-
# r210g: hub_files 族 / workshop 端点 调用上下文深挖（为 r211 备料）
import io, os, re
d = 'D:/scan/figma_report/_js'
files = []
for root, dirs, fs in os.walk(d):
    for fn in fs:
        if fn.endswith('.js'):
            files.append(os.path.join(root, fn))
print('js files =', len(files), flush=True)

KEY = ['/api/hub_files/', '/api/resource_uses/hub_file', 'prepare_insert', 'template_canvas',
       'workshop', 'resource_uses/hub']
out = []
for f in files:
    try:
        s = io.open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    hits = [k for k in KEY if k in s]
    if not hits:
        continue
    out.append('== %s :: %s' % (os.path.basename(f), ','.join(hits)))
    for k in hits[:3]:
        for m in list(re.finditer(re.escape(k), s))[:2]:
            i = m.start()
            seg = s[max(0, i - 170):i + 260].replace('\n', ' ')
            out.append('   [%s] >>> %s' % (k, seg[:420]))
    out.append('')

io.open('_r210g_hubctx_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('saved _r210g_hubctx_out.txt lines=', len(out))
# 控制台打前 100 行
for line in out[:100]:
    print(line)
print('DONE210g')
