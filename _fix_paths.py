# -*- coding: utf-8 -*-
import io
for f in ['_x_n10.py', '_x_n11.py', '_x_n12.py', '_x_n13.py']:
    s = io.open(f, encoding='utf-8').read()
    s2 = s.replace(r'F:\scan', r'D:\scan')
    io.open(f, 'w', encoding='utf-8', newline='').write(s2)
    print(f, 'changed' if s != s2 else 'nochange')
