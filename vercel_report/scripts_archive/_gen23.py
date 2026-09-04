# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v23j').replace('vda19_exec_chain_guest.py', 'vda23_descriptor_guest.py').replace('V19F_DONE', 'V23J_DONE')
open('_run_v23j.py', 'w', encoding='utf-8').write(src)
print('gen ok')
