# -*- coding: utf-8 -*-
"""q36: 候选目标 JS 构造侦察 — videos / home_shelf / pinned / tagged_file / code_connect / notification_settings"""
import io, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

def read(p):
    try: return io.open(p, encoding='utf-8', errors='replace').read()
    except Exception: return ''

JS_DIR = '_js'
js_files = sorted(os.listdir(JS_DIR))
targets = ['videos/', 'home_shelf', 'tagged_file', 'code_connect', 'notification_settings', 'resources/pinned', 'hub_file_duplicates']

cache = {}
def getj(f):
    if f not in cache: cache[f] = read(os.path.join(JS_DIR, f))
    return cache[f]

seen = set()
for t in targets:
    print('=' * 30, t)
    cnt = 0
    for jf in js_files:
        js = getj(jf)
        if t not in js: continue
        for m in re.finditer(re.escape(t), js):
            start = max(0, m.start() - 700)
            end = m.end() + 1200
            seg = js[start:end].replace('\n', ' ')
            key = (t, seg[:200])
            if key in seen: continue
            seen.add(key)
            print(f'--- [{jf}] ...{seg[:1600]}...')
            cnt += 1
            break
        if cnt >= 2: break
    print()
