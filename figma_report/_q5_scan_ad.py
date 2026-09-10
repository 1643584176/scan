# -*- coding: utf-8 -*-
# 扫描 _r196ad_ad*.txt 头部
import io, glob, os
d = os.path.dirname(os.path.abspath(__file__))
for f in sorted(glob.glob(os.path.join(d, '_r196ad_ad*.txt'))):
    bn = os.path.basename(f)
    try:
        head = io.open(f, encoding='utf-8', errors='replace').read(300)
    except Exception as e:
        head = str(e)
    head = head.replace('\n', ' | ')
    print(bn, '::', head[:220])
    print()
