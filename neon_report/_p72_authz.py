# -*- coding: utf-8 -*-
"""prod_app.js + index: Authorization 注入 / _8() CSRF 来源 / axios 拦截器"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
out = []
for fn in ['prod_app.js', 'prod_chunks/index-LpJ7SKi1.js']:
    p = os.path.join(here, '_js', fn)
    src = open(p, encoding='utf-8', errors='replace').read()
    out.append('===== %s =====' % fn)
    for kw in ['Authorization', 'Bearer ', 'X-CSRF-Token', 'interceptors', 'withCredentials']:
        idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
        out.append('KW %s -> %d' % (kw, len(idxs)))
        for i in idxs[:6]:
            seg = src[max(0, i - 200):i + 250].replace('\n', ' ')
            out.append('  ctx: ' + seg[:400])
open(os.path.join(here, '_p72_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
