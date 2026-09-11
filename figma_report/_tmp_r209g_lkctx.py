# -*- coding: utf-8 -*-
# r209g: 提取 _r202_folder_634606970.txt 中 lk- 上下文与字段名
import io, os, re
d = os.path.dirname(os.path.abspath(__file__))
txt = io.open(os.path.join(d, '_r202_folder_634606970.txt'), encoding='utf-8', errors='replace').read()

out = []
for m in re.finditer(r'lk-[0-9a-f]{40,}', txt):
    i = m.start()
    seg = txt[max(0, i-260):i+120].replace('\n', ' ')
    out.append('>>> ' + seg)
    out.append('---')

io.open(os.path.join(d, '_r209g_lkctx_out.txt'), 'w', encoding='utf-8').write('\n'.join(out[:60]))
print('total lk occurrences:', len(re.findall(r'lk-[0-9a-f]{40,}', txt)))
print('lines:', len(out))
