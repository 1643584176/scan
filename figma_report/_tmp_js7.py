# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('##### file_versions 上下文 #####')
for m in list(re.finditer('file_versions', t))[:6]:
    a = max(0, m.start() - 350); b = min(len(t), m.end() + 350)
    print(f'--- @{m.start()} ---'); print(t[a:b].replace('\n',' ')); print()
print('##### /api/versions/ 上下文 #####')
for m in list(re.finditer(re.escape('/api/versions/'), t))[:6]:
    a = max(0, m.start() - 350); b = min(len(t), m.end() + 350)
    print(f'--- @{m.start()} ---'); print(t[a:b].replace('\n',' ')); print()
