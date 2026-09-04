# -*- coding: utf-8 -*-
"""由 fnup17 生成 fnup18(部署 probe10)"""
s = open(r'D:\scan\netlify_report\_net_fnup17.py', encoding='utf-8').read()
s = s.replace("name = 'probe-log'", "name = 'probe10'")
s = s.replace("'fn-plog'", "'fn-p10'")
s = s.replace("_last_did2.txt", "_last_did3.txt")
open(r'D:\scan\netlify_report\_net_fnup18.py', 'w', encoding='utf-8').write(s)
print('written')
