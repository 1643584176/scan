# -*- coding: utf-8 -*-
"""考古 916129 模块定义 (main JS) + restore 端点 URL 形态"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()
print(f'main len={len(data)}')

# 1. webpack 模块定义 916129:function / 916129:( / 916129:e =>
for pat in [r'916129:\s*(?:function|\(|async|e\s*=>)', r',916129:\s*function', r'\.916129\s*=']:
    for m in list(re.finditer(pat, data))[:3]:
        s = m.start()
        print(f'DEF@ {s}: {data[s:s+600]}')
        print('---')

# 2. restore version API URL (9300 里 tn 是 restore 触发, 找 URL)
print()
print('===== restore url patterns in 9300 =====')
p9300 = os.path.join(JS, '9300-41a18cb0f8ba922b.min.js')
d93 = open(p9300, encoding='utf-8', errors='replace').read()
for pat in [r'[/"\x60]api[^"\x60]{0,80}restore[^"\x60]{0,40}', r'[/"\x60]restore[^"\x60]{0,60}']:
    for m in list(re.finditer(pat, d93))[:5]:
        s = max(0, m.start() - 150)
        e = min(len(d93), m.end() + 100)
        print(f'9300 {pat[:20]}@ {m.start()}: {d93[s:e][:300]}')
        print('---')
print('ALL DONE')
