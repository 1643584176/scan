# -*- coding: utf-8 -*-
# q8: 挖 DEV_MODE_FILE_SEEN / DESIGN_FILE_SEEN 枚举值定义
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

kws = ['DEV_MODE_FILE_SEEN', 'DESIGN_FILE_SEEN', 'FILE_SEEN', 'Mr=', 'FILE_VISITED']
out = []
for k in kws:
    idxs = [m.start() for m in re.finditer(re.escape(k), JS)]
    out.append('===== %s :: %d hits =====' % (k, len(idxs)))
    for i in idxs[:16]:
        seg = JS[max(0, i - 210):i + 300].replace('\n', ' ')
        out.append('  >>> ' + seg)
    out.append('')
io.open(os.path.join(d, '_q8_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
for k in kws:
    print(k, len(re.findall(re.escape(k), JS)))
print('DONE -> _q8_out.txt')
