# -*- coding: utf-8 -*-
# r197 对照: C 组 body 逐字节比对
import hashlib

def body(p):
    d = open(p, 'rb').read().split(b'\n', 1)
    return d[1] if len(d) > 1 else b''

for f in ['C1_base', 'C2_ref', 'C3_arith', 'C4_frag']:
    b = body('_r197_%s.txt' % f)
    print(f, len(b), hashlib.md5(b).hexdigest(), flush=True)

b1 = body('_r197_C1_base.txt')
for f in ['C2_ref', 'C3_arith', 'C4_frag']:
    b = body('_r197_%s.txt' % f)
    d = next((i for i, (x, y) in enumerate(zip(b1, b)) if x != y), -1)
    print('first-diff', f, ('SAME' if d == -1 and len(b1) == len(b) else d), flush=True)

# C1 结构摘要: 顶层 keys + 列表型字段的条数
import json
j = json.loads(b1.decode('utf-8'))
print('C1 top keys:', list(j.keys()), flush=True)
meta = j.get('meta')
if isinstance(meta, dict):
    print('C1 meta keys:', list(meta.keys())[:15], flush=True)
    for k, v in meta.items():
        if isinstance(v, list):
            print('  meta.%s = [%d]' % (k, len(v)), flush=True)
    files = meta.get('files')
    if isinstance(files, list) and files:
        first = files[0]
        if isinstance(first, dict):
            print('  first file keys:', list(first.keys())[:12], flush=True)
