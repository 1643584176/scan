# -*- coding: utf-8 -*-
p = r'D:\scan\_run_v57.py'
out = r'D:\scan\_run_v58.py'
s = open(p, encoding='utf-8').read()
s = s.replace('v57', 'v58')
s = s.replace("GUEST = 'vda58_ctr_verify_guest.py'", "GUEST = 'vda58_ctr_fix_guest.py'")
open(out, 'w', encoding='utf-8').write(s)
print('run_v58 written')
