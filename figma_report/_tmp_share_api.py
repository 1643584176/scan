# -*- coding: utf-8 -*-
"""找共享线程动作的端点/API(privacyMode 修改、share thread)+ 创建线程 REST/livegraph mutation"""
import os, re

JS = r'F:/scan/figma_report/_js'
ALL = {}
for fn in os.listdir(JS):
    if fn.endswith('.js'):
        try:
            ALL[fn] = open(os.path.join(JS, fn), encoding='utf-8', errors='ignore').read()
        except Exception:
            pass

print('=== privacyMode 写入相关 API(share/update) ===')
for fn, c in ALL.items():
    for m in re.finditer(r'[^,;{}]{0,100}(?:privacyMode|shareThread|thread_privacy|privacy)[^,;{}]{0,60}(?:update|set|share|mutat|api|fetch|POST|PUT)[^,;{}]{0,100}', c):
        g = m.group(0)
        if any(k in g for k in ['api', 'mutat', 'fetch', 'updateThread', 'shareThread']):
            print(f'-- {fn}: {g[:260].replace(chr(10), " ")}')
            break  # 每文件一处即可

print()
print('=== ai_assistant 相关 REST/action 路径 ===')
seen = set()
for fn, c in ALL.items():
    for m in re.finditer(r'["\'](/api/[A-Za-z0-9_/${}.\-]*ai[A-Za-z0-9_/${}.\-]*)["\']', c, re.I):
        g = m.group(1)
        if g not in seen and ('thread' in g.lower() or 'chat' in g.lower() or 'assist' in g.lower()):
            seen.add(g)
            print(f'-- {fn}: {g}')

print()
print('=== create thread mutation 上下文(main 中 ai_assistant_create_thread) ===')
c = ALL.get('figma_app-main.js', '')
for m in list(re.finditer(r'[^,;{}]{0,200}ai_assistant_create_thread[^,;{}]{0,300}', c))[:4]:
    print('   ', m.group(0)[:480].replace('\n', ' '))
