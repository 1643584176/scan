# -*- coding: utf-8 -*-
src = open('_run_v33s.py', encoding='utf-8').read()
src = src.replace('v33s', 'v34s').replace('vda33_share_probe_guest.py', 'vda34_ctrd_create_guest.py').replace('V33S_DONE', 'V34S_DONE')
open('_run_v34s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
