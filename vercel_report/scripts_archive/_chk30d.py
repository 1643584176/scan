# -*- coding: utf-8 -*-
txt = open('_run_v30q_out.txt', encoding='utf-8', errors='replace').read()
i = txt.find('iner ===')
print('first at', i)
print(repr(txt[max(0, i - 600):i + 200]))
# 找所有 data 行
import re
for m in re.finditer(r'wait r(\d+) status=200 \| (.{0,400})', txt):
    print('r%s: %r' % (m.group(1), m.group(2)[-150:]))
    if int(m.group(1)) > 3:
        break
