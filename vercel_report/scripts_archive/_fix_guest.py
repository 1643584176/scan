# -*- coding: utf-8 -*-
p = r'D:\scan\_run_v57.py'
s = open(p, encoding='utf-8').read()
s = s.replace("GUEST = 'vda55_ctr_diag_guest.py'", "GUEST = 'vda57_ctr_verify_guest.py'")
open(p, 'w', encoding='utf-8').write(s)
print('GUEST fixed ->', s.splitlines()[10:14])
