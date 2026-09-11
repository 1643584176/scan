# -*- coding: utf-8 -*-
# q79: 传输层变异历史核查——form/multipart/%2527/数组语法 是否打过
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
py = [f for f in glob.glob(os.path.join(D, '_*.py')) if '_q79' not in f]

patterns = {
    'form-urlencoded': r'x-www-form-urlencoded',
    'multipart': r'multipart',
    'urlencode()调用': r'urlencode\(',
    'data=传参': r'\bdata\s*=\s*[^N]',
    '%2527双重编码': r'%2527',
    '数组语法[]=': r'\[\]=',
    'JSON数组值': r'\[\s*[\'"]',
    'GET带body': r'requests\.get\([^)]+data=',
}
for name, p in patterns.items():
    cnt = 0; files = set(); sample = ''
    for f in py:
        try: t = open(f, encoding='utf-8', errors='replace').read()
        except: continue
        ms = list(re.finditer(p, t))
        if ms:
            cnt += len(ms); files.add(os.path.basename(f))
            if not sample:
                i = ms[0].start(); sample = f'{os.path.basename(f)}: {t[max(0,i-100):i+120]}'.replace('\n', ' ')
    print(f'  {name:18s} hits={cnt:4d} files={len(files):3d}  {sample[:200]}')
    if files:
        print(f'      files: {sorted(files)[:8]}')
print('DONE q79')
