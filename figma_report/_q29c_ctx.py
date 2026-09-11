# -*- coding: utf-8 -*-
import io, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

checks = [
 ('buzz', '_figma_q10_apiparams.py'), ('buzz', '_figma_r196e_reqid.py'), ('buzz', '_figma_r196g_buzzplan.py'),
 ('buzz', '_figma_r85_rt.py'), ('buzz', '_figma_r87_fast.py'), ('buzz', '_tmp_ls5.py'),
 ('color_palette', '_figma_r112.py'), ('color_palette', '_figma_r119.py'), ('color_palette', '_figma_r121.py'),
 ('color_palette', '_figma_r196ab_perm.py'),
 ('buzz_approvals', '_tmp_ls5.py'),
]
for rx, f in checks:
    try: t = io.open(f, encoding='utf-8', errors='replace').read()
    except Exception as e:
        print(f, 'ERR', e); continue
    for m in re.finditer(re.escape(rx), t):
        s = max(0, m.start() - 130); e = m.end() + 130
        seg = t[s:e].replace('\n', ' | ')
        print(f'--- {f} [{rx}]')
        print(f'    ...{seg}...')
        break
