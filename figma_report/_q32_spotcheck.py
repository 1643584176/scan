# -*- coding: utf-8 -*-
"""q32: 抽查 used_L1 可疑 key 的实际上下文"""
import io, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

def read(p):
    try: return io.open(p, encoding='utf-8', errors='replace').read()
    except Exception: return ''

files = [f for f in os.listdir('.') if f.endswith('.py') and
         (f.startswith('_figma_') or f.startswith('_tmp_')) and not re.match(r'_q\d', f)]

suspects = ['desc', 'fv', 'fk', 'caller', 'fuid', 'max_num_results', 'secondary_user_id',
            'viewer_export_restricted', 'value', 'field_schema_id', 'primary_user_id', 'before']
for key in suspects:
    rx = re.compile(r'[?&]' + re.escape(key) + r'=')
    shown = 0
    print(f'===== {key} =====')
    for f in files:
        t = read(f)
        for m in rx.finditer(t):
            s = max(0, m.start() - 90); e = m.end() + 60
            seg = t[s:e].replace('\n', ' ')
            print(f'  [{f}] ...{seg}...')
            shown += 1
            break
        if shown >= 2: break
    if shown == 0: print('  (无)')
    print()
