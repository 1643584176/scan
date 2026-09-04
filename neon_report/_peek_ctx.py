# -*- coding: utf-8 -*-
import json, os
base = r'D:\scan\neon_report'
for f in ['_ctx.json', '_ctx_b.json', '_na_orgctx.json', '_na_sess.json', '_na_tokens.json', '_auth_better_auth.json']:
    p = os.path.join(base, f)
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding='utf-8'))
            s = json.dumps(d, ensure_ascii=False)
            print('== %s (%d B)' % (f, len(s)))
            print(s[:600])
        except Exception as e:
            print('== %s ERROR %s' % (f, e))
    else:
        print('== %s NOT FOUND' % f)
