# -*- coding: utf-8 -*-
src = open('_run_v34s.py', encoding='utf-8').read()
src = src.replace('v34s', 'v35s').replace('vda34_ctrd_create_guest.py', 'vda35_ctrd_create2_guest.py').replace('V34S_DONE', 'V35S_DONE')
open('_run_v35s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
