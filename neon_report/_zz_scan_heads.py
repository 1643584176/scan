# -*- coding: utf-8 -*-
"""扫 Beta 面测试脚本的头部注释,判断覆盖面与结论"""
import glob, os, re

pats = ['_n1*', '_n2*', '_n3*', '_n4*', '_f1b*', '_f1c*', '_f1d*', '_f1_mkzip*', '_f1_deploy*',
        '_f2_cred*', '_f3_cred*', '_na_userface*', '_na_setup*', '_chk_creds*', '_f4_share*',
        '_f5_cleanup*', '_f2b*', '_f4b*']
seen = set()
for p in pats:
    for f in sorted(glob.glob(os.path.join(r'D:\scan\neon_report', p))):
        if f in seen or not f.endswith('.py'):
            continue
        seen.add(f)
        try:
            t = open(f, encoding='utf-8', errors='ignore').read(600)
            # 提取注释/docstring 头
            head = ' '.join(t.splitlines()[:8])[:260]
            print('###', os.path.basename(f))
            print('   ', head)
        except Exception as e:
            print('###', f, 'ERR', e)
