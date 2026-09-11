# -*- coding: utf-8 -*-
# r210d: 历史覆盖检查（CMS 结构族 / claim / mark / export / comments 写）
import os, io
d = 'D:/scan/figma_report'
kws = ['createCollection', 'exportAsCsv', 'field_schemas', 'createFieldSchema',
       'updateFieldSchema', 'deleteFieldSchema', 'mark_diagram', 'file/claim',
       'claimTryFile', 'resolved_at', 'client_meta', 'message_meta',
       'comments/${', 'databaseId']
hits = {k: [] for k in kws}
for root, dirs, files in os.walk(d):
    for fn in files:
        if not fn.endswith('.py'):
            continue
        p = os.path.join(root, fn)
        try:
            s = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for k in kws:
            if k in s:
                hits[k].append(fn)
for k in kws:
    print('==', k, '::', len(hits[k]))
    for f in sorted(hits[k])[:14]:
        print('   ', f)
