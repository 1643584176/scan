# -*- coding: utf-8 -*-
# q81: 「注释/特殊字符/合并」三方向历史覆盖核查——找真空白细分形态
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
py = [f for f in glob.glob(os.path.join(D, '_*.py')) if '_q81' not in f]

pats = {
    '内联注释 /**/': r'/\*\*?/|%2f\*|\*%2f',
    '注释+换行 --%0a': r'--%0[aAdD]|%0[ad]%20--|--\\n',
    '中文注释 #c': r'[?&][a-z_]+=1%23|%23--',
    'PG :: 转换': r'%3A%3A|::int|::text|=%27::',
    'PG $$ 引用': r'%24%24|=\$\$|\$\$1',
    'PG || 拼接': r'%7C%7C|\|\|',
    'U+2028/2029': r'%E2%80%A8|%E2%80%A9|2028|2029',
    '控制符%01': r'%01|=.*%1[fF]',
    '逗号合并值': r'[a-z_]+=[a-z]+,(asc|desc|name|team)',
    'sort_column HPP': r'sort_column=[^&]+&[^&]*sort_column=',
    '值藏编码&': r'%26[a-z_]+%3D',
    '方括号名语法': r'\[\]=|%5B',
}
for name, p in pats.items():
    cnt = 0; files = set(); samples = []
    for f in py:
        try: t = open(f, encoding='utf-8', errors='replace').read()
        except: continue
        ms = list(re.finditer(p, t))
        if ms:
            cnt += len(ms); files.add(os.path.basename(f))
            if len(samples) < 2:
                i = ms[0].start()
                samples.append(f'{os.path.basename(f)}: {t[max(0,i-90):i+90]}'.replace('\n', ' '))
    print(f'== {name}: hits={cnt} files={len(files)}')
    for s in samples:
        print(f'   {s[:200]}')
print('DONE q81')
