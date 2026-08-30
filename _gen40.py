# -*- coding: utf-8 -*-
src = open('_run_v39s.py', encoding='utf-8').read()
src = src.replace('v39s', 'v40s').replace('vda39_persist_check_guest.py', 'vda40_exec_fix_guest.py').replace('V39S_DONE', 'V40S_DONE')
open('_run_v40s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
