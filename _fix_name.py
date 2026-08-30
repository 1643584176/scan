# -*- coding: utf-8 -*-
"""fix NAME quotes in _run_v43b.py"""
p = r'F:\scan\_run_v43b.py'
s = open(p, encoding='utf-8').read()
s = s.replace('NAME = v43b', "NAME = 'v43b'")
open(p, 'w', encoding='utf-8').write(s)
print('fixed')
