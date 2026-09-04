# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v26m').replace('vda19_exec_chain_guest.py', 'vda26_curl_h2_guest.py').replace('V19F_DONE', 'V26M_DONE')
open('_run_v26m.py', 'w', encoding='utf-8').write(src)
print('gen ok')
