# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v21h').replace('vda19_exec_chain_guest.py', 'vda21_field_probe_guest.py').replace('V19F_DONE', 'V21H_DONE')
open('_run_v21h.py', 'w', encoding='utf-8').write(src)
print('gen ok')
