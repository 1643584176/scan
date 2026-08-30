# -*- coding: utf-8 -*-
src = open('_run_v38s.py', encoding='utf-8').read()
src = src.replace('v38s', 'v39s').replace('vda38_ctrd_create5_guest.py', 'vda39_persist_check_guest.py').replace('V38S_DONE', 'V39S_DONE')
open('_run_v39s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
