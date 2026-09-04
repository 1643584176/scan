# -*- coding: utf-8 -*-
"""解析 probe4 输出:extension 结构 / proc2 / 网络连接"""
import json

d = json.load(open(r'D:\scan\netlify_report\_probe4_out.json', encoding='utf-8'))
for k, v in d.items():
    if k in ('proc1', 'proc9'):
        print('=== %s ===' % k)
        for kk, vv in v.items():
            print(' %s: %s' % (kk, str(vv)[:800]))
    elif k in ('extFiles', 'tmpReqFiles'):
        print('=== %s ===' % k)
        for x in v:
            print(' ', str(x)[:600])
    elif k == 'extDir':
        print('extDir:', v)
    else:
        print('=== %s ===' % k)
        print(str(v)[:2500])
