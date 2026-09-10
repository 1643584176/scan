# -*- coding: utf-8 -*-
# q7: JS 挖 activity_type 枚举 + postRecentActivity 调用点 + related_links 计划门线索
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

kws = ['postRecentActivity', 'activity_type', "'VIEWED'", 'RecentActivity',
       'recent_activity']
out = []
for k in kws:
    idxs = [m.start() for m in re.finditer(re.escape(k), JS)]
    out.append('===== %s :: %d hits =====' % (k, len(idxs)))
    for i in idxs[:14]:
        seg = JS[max(0, i - 170):i + 260].replace('\n', ' ')
        out.append('  >>> ' + seg)
    out.append('')
io.open(os.path.join(d, '_q7_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
for k in kws:
    print(k, len(re.findall(re.escape(k), JS)))
print('DONE -> _q7_out.txt')
