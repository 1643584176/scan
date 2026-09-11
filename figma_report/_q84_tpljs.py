# -*- coding: utf-8 -*-
# q84: 等待 hub 冷却期间——JS 深挖：team templates 列表端点 / hub 面其余端点 / fv 真实来源
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report\_js'
s = io.open(D + r'\figma_app-main.js', encoding='utf-8', errors='replace').read()

def dump(key, before=200, after=300, limit=5):
    ms = list(re.finditer(re.escape(key), s))
    print('\n== %s : %d hits ==' % (key, len(ms)))
    for m in ms[:limit]:
        i = m.start()
        seg = s[max(0, i - before):i + after].replace('\n', ' ')
        print('   >>>', seg[:500])

for k in ['getFilteredTeamTemplates', 'team_templates', 'getTeamTemplates',
          'filterable_teams', 'template_type', 'teamTemplateId', 'team_template_id']:
    dump(k)

# fv 来源：fileVersion 从哪来
print('\n\n===== fileVersion 相关 =====')
for m in list(re.finditer(r'fileVersion', s))[:8]:
    i = m.start()
    print('   fV >>>', s[max(0, i - 150):i + 150].replace('\n', ' ')[:300])
