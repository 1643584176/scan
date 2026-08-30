# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v22i').replace('vda19_exec_chain_guest.py', 'vda22_grpc_probe_guest.py').replace('V19F_DONE', 'V22I_DONE')
open('_run_v22i.py', 'w', encoding='utf-8').write(src)
print('gen ok')
