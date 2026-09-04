# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v24k').replace('vda19_exec_chain_guest.py', 'vda24_field_enum_guest.py').replace('V19F_DONE', 'V24K_DONE')
open('_run_v24k.py', 'w', encoding='utf-8').write(src)
print('gen ok')
