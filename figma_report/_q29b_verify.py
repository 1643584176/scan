# -*- coding: utf-8 -*-
import io, glob, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

targets = {
 'videos 端点': r'videos/\$\{',
 'github-app': r'github-app',
 'buzz': r'buzz',
 'color_palette': r'color_palette',
 'supabase secrets': r'integrations/supabase',
 'buzz_approvals': r'buzz_approvals',
}
files = [f for f in os.listdir('.') if f.endswith('.py') and not f.startswith('_q2') and f != '_q29_check_r196.py']
print(f'scan {len(files)} py files')
for name, rx in targets.items():
    hits = []
    for f in files:
        try: t = io.open(f, encoding='utf-8', errors='replace').read()
        except Exception: continue
        n = len(re.findall(rx, t))
        if n: hits.append(f'{f}({n})')
    print(f'== {name}: {hits[:8] if hits else "ZERO"}')
