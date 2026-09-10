# -*- coding: utf-8 -*-
# g6: 提取关键历史脚本的头部注释(SQLi 面结论素材)
import os, io
d = os.path.dirname(os.path.abspath(__file__))
scripts = ['_figma_r111d.py', '_figma_r143_sb.py', '_figma_r154_pathinj.py',
           '_figma_r156_hubprof.py', '_figma_r167_newfaces_inj.py',
           '_figma_r194g_cms_slots.py', '_figma_r194j_cms_csvval.py',
           '_figma_r195b_hs_pinned.py', '_figma_r195c_pinned.py',
           '_figma_r196i_trashinj.py', '_figma_r196j_strongbool.py',
           '_figma_r196o_planai.py', '_figma_r196ab_perm.py']
for f in scripts:
    p = os.path.join(d, f)
    if not os.path.exists(p):
        print('MISS', f); continue
    lines = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
    head = [l for l in lines[:8]]
    print('=' * 70)
    print(f)
    for l in head:
        print('   ', l[:160])
