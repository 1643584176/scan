# -*- coding: utf-8 -*-
src = open('skills/non-traditional-vuln-hunting/vda27_ctrd_probe_guest.py', encoding='utf-8').read()
src = src.replace('vda27_ctrd_probe', 'vda28_ctrd2').replace('V27N_DONE', 'V28O_DONE').replace('v27n.out', 'v28o.out')
src = src.replace(csp
