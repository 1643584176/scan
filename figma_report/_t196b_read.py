# -*- coding: utf-8 -*-
# t196b: 读 WS 错误响应 + 从 w1 提取 stableId / 数据结构
import io, re
for f in ['_r196b_w2.json', '_r196b_w4.json', '_r196b_w6.json']:
    print('=====', f)
    print(io.open(f, encoding='utf-8', errors='replace').read()[:950])
    print()
big = io.open('_r196b_w1.json', encoding='utf-8', errors='replace').read()
for pat in [r'"itemStableId":"([^"]{3,80})"', r'"stableId":"([^"]{3,80})"',
            r'"collectionStableId":"([^"]{3,80})"']:
    vs = re.findall(pat, big)
    print(pat, 'n=', len(vs), vs[:10])
print('== w1 lines summary')
for i, line in enumerate(big.split('\n')):
    print(f'L{i} len={len(line)} head={line[:120]!r}')
print('DONE')
