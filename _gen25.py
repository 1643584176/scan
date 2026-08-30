# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v25l').replace('vda19_exec_chain_guest.py', 'vda25_light_desc_guest.py').replace('V19F_DONE', 'V25L_DONE')
open('_run_v25l.py', 'w', encoding='utf-8').write(src)
print('gen ok')
