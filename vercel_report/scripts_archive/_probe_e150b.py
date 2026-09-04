# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
data = open(r'D:\scan\_e150_read_out.txt', 'rb').read()
for enc in ('utf-8', 'gbk', 'gb18030'):
    try:
        t = data.decode(enc)
        break
    except Exception:
        continue
print(t)
