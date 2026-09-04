# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v29p').replace('vda19_exec_chain_guest.py', 'vda29_ctrd_h2_guest.py').replace('V19F_DONE', 'V29P_DONE')
open('_run_v29p.py', 'w', encoding='utf-8').write(src)
print('gen ok')
