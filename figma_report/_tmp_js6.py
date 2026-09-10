# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
# webpack 模块定义模式:916428(e,t,r){ 或 916428:(...) 或 916428=>
for pat in (r'916428\s*[:(]', r'916428\s*=\s*>', r'getPaginatedVersions\s*[:(=]'):
    print(f'##### pattern {pat} #####')
    n = 0
    for m in re.finditer(pat, t):
        a = max(0, m.start() - 200)
        b = min(len(t), m.end() + 800)
        print(f'--- @{m.start()} ---')
        print(t[a:b].replace('\n', ' ')[:1000])
        print()
        n += 1
        if n >= 3: break
