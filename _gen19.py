# -*- coding: utf-8 -*-
src = open('_run_v18e.py', encoding='utf-8').read()
src = src.replace('v18e', 'v19f').replace('vda18_stream_fields_guest.py', 'vda19_exec_chain_guest.py').replace('V18E_DONE', 'V19F_DONE')
open('_run_v19f.py', 'w', encoding='utf-8').write(src)
print('ok')
