# -*- coding: utf-8 -*-
# g3: 验证 r196q_links1.py 与 r196ao_links1.py 是否同内容(改名残留判定)
import hashlib, os
a = '_figma_r196q_links1.py'
b = '_figma_r196ao_links1.py'
ha = hashlib.md5(open(a, 'rb').read()).hexdigest()
hb = hashlib.md5(open(b, 'rb').read()).hexdigest()
print(a, ha)
print(b, hb)
print('SAME' if ha == hb else 'DIFF')
if ha == hb:
    os.remove(a)
    print('removed:', a)
