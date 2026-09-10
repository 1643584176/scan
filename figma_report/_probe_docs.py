# -*- coding: utf-8 -*-
"""读取 z 系列脚本 docstring, 快速了解测试覆盖面"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = ['_figma_z17_msgs.py', '_figma_z20_views.py', '_figma_z21_ws.py', '_figma_z22_multi.py',
         '_figma_z23_mowner.py', '_figma_z24_diff.py', '_figma_z25_canvas.py', '_figma_z26_fv.py',
         '_figma_z27_canvas2.py', '_figma_z28_figdl.py', '_figma_z29_anon_chain.py', '_figma_z30_strings.py',
         '_figma_z31_arch.py', '_figma_z32_ctrl.py', '_figma_z33_arch2.py', '_figma_z34_slc.py',
         '_figma_z35_restrict.py', '_figma_z36_share.py', '_figma_w15_removemember.py', '_figma_w17_anonmembers.py']
for f in files:
    try:
        lines = open(f, encoding='utf-8', errors='replace').read().splitlines()
        doc = [l for l in lines[1:10] if l.strip().startswith(('"""', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.'))]
        print(f'=== {f}')
        for l in lines[1:8]:
            print('   ', l)
    except Exception as e:
        print(f'=== {f} ERR {e}')
print('ALL DONE')
