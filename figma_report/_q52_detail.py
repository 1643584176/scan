# -*- coding: utf-8 -*-
# q52: 细查疑似已打的脚本内容（身份参数/recipients真值/ntype科学计数）
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def show(fname, patterns, ctx=1):
    print(f'\n===== {fname} =====')
    try:
        lines = open(fname, encoding='utf-8', errors='replace').readlines()
    except Exception as e:
        print(f'  读取失败: {e}'); return
    hit = 0
    for i, ln in enumerate(lines):
        for p in patterns:
            if p in ln:
                lo = max(0, i - ctx); hi = min(len(lines), i + ctx + 1)
                for j in range(lo, hi):
                    print(f'  {j+1}: {lines[j].rstrip()[:150]}')
                hit += 1
                break
        if hit >= 12:
            print('  ...(截断)'); break
    if hit == 0:
        print('  (无命中)')

show('_figma_r209e_inject.py', ['user_id', 'actor_id', 'impersonat', 'as_user'])
show('_figma_r216_verdict.py', ['recipients'])
show('_figma_r214a_notif_deep.py', ['junk', 'ntype'])
show('_figma_r203_edge.py', ['sci', 'e18', 'e+', 'e-'])
show('_figma_r210_diag.py', ['user/state', 'fuid'])
