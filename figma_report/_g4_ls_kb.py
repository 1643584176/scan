# -*- coding: utf-8 -*-
# g4: 列出 SQL注入经验库 目录文件
import os
d = r'D:\scan\经验\全局经验\SQL注入经验库'
for root, dirs, files in os.walk(d):
    print('DIR:', root)
    for f in files:
        p = os.path.join(root, f)
        print('  %8d  %s' % (os.path.getsize(p), f))
