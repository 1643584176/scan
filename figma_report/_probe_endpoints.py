# -*- coding: utf-8 -*-
"""全量端点提取(161 chunk): 筛 profile/community/hub 相关未测端点"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + [f for f in os.listdir(JS) if f.endswith('.min.js')]
cnt = {}
for fn in files:
    try:
        data = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r'[/"\x60](api/[a-zA-Z0-9_${}./\-]*(?:profile|plugin|widget|community|resource|publisher)[a-zA-Z0-9_${}./\-]*)[/"\x60]', data):
        ep = m.group(1)
        # 归一化: 去掉参数变量
        norm = re.sub(r'\$\{[^}]+\}', '{}', ep)
        norm = re.sub(r'/(api|community|plugin|widget|profile|publishers|versions|resources)[^/]*', r'/\1', norm)
        cnt.setdefault(norm, []).append(fn)

# 输出按频率
for ep, fl in sorted(cnt.items(), key=lambda x: -len(x[1])):
    print(f'{len(fl):3d}  {ep}')
print(f'TOTAL {len(cnt)}')
print('ALL DONE')
