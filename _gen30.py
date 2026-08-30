# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
src = src.replace('v19f', 'v30q').replace('vda19_exec_chain_guest.py', 'vda30_ctrd_deep_guest.py').replace('V19F_DONE', 'V30Q_DONE')
open('_run_v30q.py', 'w', encoding='utf-8').write(src)
print('gen ok')
