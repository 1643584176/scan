# -*- coding: utf-8 -*-
src = open('_run_v36s.py', encoding='utf-8').read()
src = src.replace('v36s', 'v37s').replace('vda36_ctrd_create3_guest.py', 'vda37_ctrd_create4_guest.py').replace('V36S_DONE', 'V37S_DONE')
open('_run_v37s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
