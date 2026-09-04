# -*- coding: utf-8 -*-
import re
d = open(r'D:\scan\figma_report\_kiwi_ref\lib\scenegraph.mjs', encoding='utf-8').read()
print('len', len(d))
for kw in ['import ', 'decodeKiwi', 'kiwi', 'generateDecoder', 'schema']:
    idx = [m.start() for m in re.finditer(re.escape(kw), d)]
    print(kw, len(idx))
for m in re.finditer(r'import[^;]+;', d):
    print('IMP:', m.group(0)[:200])
