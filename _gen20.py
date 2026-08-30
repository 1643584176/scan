# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v20g').replace('vda19_exec_chain_guest.py', 'vda20_exec_json_guest.py').replace('V19F_DONE', 'V20G_DONE')
open('_run_v20g.py', 'w', encoding='utf-8').write(src)
print('gen ok')
