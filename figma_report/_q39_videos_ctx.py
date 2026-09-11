# -*- coding: utf-8 -*-
"""q39: videos 时间戳参数 + supabase secrets 真实构造提取"""
import io, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

JS_DIR = '_js'
js_files = sorted(os.listdir(JS_DIR))
targets = ['start_timestamp_ms', 'end_timestamp_ms', 'max_results', 'secret_name']

def read(p):
    try: return io.open(p, encoding='utf-8', errors='replace').read()
    except Exception: return ''

for t in targets:
    print('=' * 40, t)
    found = 0
    for jf in js_files:
        js = read(os.path.join(JS_DIR, jf))
        if t not in js: continue
        for m in re.finditer(re.escape(t), js):
            s = max(0, m.start() - 1000)
            e = m.end() + 1000
            seg = js[s:e].replace('\n', ' ')
            print(f'--- [{jf}] ...{seg[:2000]}...')
            found += 1
            break
        if found >= 3: break
    if not found: print('  (none)')
    print()
