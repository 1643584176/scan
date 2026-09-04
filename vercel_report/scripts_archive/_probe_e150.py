# -*- coding: utf-8 -*-
data = open(r'D:\scan\_e150_read_out.txt', 'rb').read()
t = None
for enc in ['utf-8', 'gbk', 'gb18030']:
    try:
        t = data.decode(enc)
        print('DECODED with', enc, 'len', len(t))
        break
    except Exception as e:
        print(enc, 'fail', e)
if t:
    print(t[:4000])
