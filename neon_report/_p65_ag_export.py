# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: export 段中 ag 的精确匹配 + head import 段检查"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

# export 段整体提取
mi = [m.start() for m in re.finditer(r'export\{', src)]
out.append('export{ positions: %s' % mi)
for pos in mi:
    seg = src[pos:pos + 40000]
    end = seg.find('}')
    seg2 = seg[:end + 1] if end > 0 else seg[:2000]
    out.append('export seg @%d len %d' % (pos, len(seg2)))
    # 找 ag 项
    for mm in re.finditer(r'(?:^|,)([^,]{0,30}?\bag\b[^,]{0,30})(?=,|$)', seg2):
        out.append('   AG-ITEM: %s' % mm.group(1).strip())
    break  # 只看第一个(可能 export 合并成一个)

# 文件里 "as ag" 所有出现
for m in re.finditer(r'as\s+ag\b', src):
    i = m.start()
    out.append('as ag @%d: %s' % (i, src[max(0, i - 200):i + 80].replace('\n', ' ')[:260]))

open(os.path.join(here, '_p65_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
