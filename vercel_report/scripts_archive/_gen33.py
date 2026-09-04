# -*- coding: utf-8 -*-
src = open('_run_v32s.py', encoding='utf-8').read()
src = src.replace('v32s', 'v33s').replace('vda32_celld_plugin_guest.py', 'vda33_share_probe_guest.py').replace('V32S_DONE', 'V33S_DONE')
open('_run_v33s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
