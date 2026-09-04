# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: 定位 np 定义(class np / const np= / np= 实例化)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

for m in re.finditer(r'(?:class|var|const|let)\s+np\b[^=]{0,10}=?', src):
    i = m.start()
    out.append('DEF @%d: %s' % (i, src[i:i + 400].replace('\n', ' ')[:380]))
# np= 实例化(前面是 const/var 已被覆盖, 这里是新实例)
for m in re.finditer(r'np\s*=\s*new\s+\w+', src):
    i = m.start()
    out.append('NEW @%d: %s' % (i, src[max(0, i - 150):i + 150].replace('\n', ' ')[:280]))
# np 出现总数
out.append('np occurrences: %d' % len(re.findall(r'\bnp\b', src)))

open(os.path.join(here, '_p66_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
