# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v27n').replace('vda19_exec_chain_guest.py', 'vda27_ctrd_probe_guest.py').replace('V19F_DONE', 'V27N_DONE')
open('_run_v27n.py', 'w', encoding='utf-8').write(src)
print('gen ok')
