# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for fn in ('_js/figma_app-main.js',):
    t = open(fn, encoding='utf-8', errors='replace').read()
    for kw in ('lookup_by_component_name', 'checkpoint_diff'):
        for m in re.finditer(re.escape(kw), t):
            a = max(0, m.start() - 400)
            b = min(len(t), m.end() + 400)
            print(f'--- {fn} @{m.start()} [{kw}] ---')
            print(t[a:b].replace('\n', ' '))
            print()
            break  # 每个文件每个关键字先看第一处
