# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('##### nodes_to_diff #####')
for m in list(re.finditer(re.escape('nodes_to_diff'), t))[:8]:
    a = max(0, m.start() - 600); b = min(len(t), m.end() + 400)
    print(f'--- @{m.start()} ---'); print(t[a:b].replace('\n',' ')); print()
print('##### who calls J: 搜 checkpointDiff / checkpointId #####')
for kw in ('checkpointId', 'checkpoint_id', 'checkpointDiff'):
    print(f'== [{kw}] ==')
    for m in list(re.finditer(re.escape(kw), t))[:5]:
        a = max(0, m.start() - 400); b = min(len(t), m.end() + 300)
        print(f'--- @{m.start()} ---'); print(t[a:b].replace('\n',' ')); print()
