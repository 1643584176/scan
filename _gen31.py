# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v31r').replace('vda19_exec_chain_guest.py', 'vda31_ctrd_fast_guest.py').replace('V19F_DONE', 'V31R_DONE')
open('_run_v31r.py', 'w', encoding='utf-8').write(src)
print('gen ok')
