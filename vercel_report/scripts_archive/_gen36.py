# -*- coding: utf-8 -*-
src = open('_run_v35s.py', encoding='utf-8').read()
src = src.replace('v35s', 'v36s').replace('vda35_ctrd_create2_guest.py', 'vda36_ctrd_create3_guest.py').replace('V35S_DONE', 'V36S_DONE')
open('_run_v36s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
