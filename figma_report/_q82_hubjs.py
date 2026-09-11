# -*- coding: utf-8 -*-
# q82: hub_files 族 JS 调用形态精确提取（为 r257 打点准备）
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

s = io.open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
print('js len =', len(s))

KEYS = ['template_canvas', 'prepare_insert', 'hub_files/v2', 'hub_files/template/',
        'resource_uses/hub_file', 'resource_uses/template', 'team_template', 'TeamTemplate']
for k in KEYS:
    ms = list(re.finditer(re.escape(k), s))
    print('\n== %s : %d hits ==' % (k, len(ms)))
    for m in ms[:4]:
        i = m.start()
        seg = s[max(0, i - 220):i + 260].replace('\n', ' ')
        print('   >>>', seg[:460])
