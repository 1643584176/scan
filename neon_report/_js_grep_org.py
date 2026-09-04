# -*- coding: utf-8 -*-
"""grep bundle:org_id 在请求里的真实位置(createProject/API client 层)"""
import re

txt = open(r'D:\scan\neon_report\_js\app.js', encoding='utf-8').read()

print('== org_id 出现次数:', len(re.findall('org_id', txt)))
# 找 createProject / project 创建的 api 调用上下文
for kw in ['createProject', 'create-project', 'postProjects', 'create_project']:
    hits = [m.start() for m in re.finditer(re.escape(kw), txt)]
    print('\n== %s hits: %d' % (kw, len(hits)))
    for i in hits[:3]:
        print(' CTX:', txt[max(0, i - 300):i + 300].replace('\n', ' ')[:550])

# org_id 首次出现上下文(可能是响应/请求构造)
idxs = [m.start() for m in re.finditer('org_id', txt)][:12]
for i in idxs:
    print('\nORG_CTX:', txt[max(0, i - 250):i + 250].replace('\n', ' ')[:480])
