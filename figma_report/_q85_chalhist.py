# -*- coding: utf-8 -*-
# q85: 历史覆盖核查——awswaf 挑战 / 202 现象 在项目历史中是否出现过
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
pats = {
    'awswaf/challenge': r'awswaf|gokuProps|token\.awswaf|challenge\.js|Javascript is disabled',
    'not a robot': r'not a robot|verify that you',
    'status 202': r'\b202\b',
}
files = []
for ext in ('*.md', '*.txt', '*.py'):
    files.extend(glob.glob(os.path.join(D, ext)))

for name, p in pats.items():
    print(f'\n===== {name} =====')
    cnt = 0
    for f in files:
        try:
            t = io.open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        ms = list(re.finditer(p, t))
        if ms:
            cnt += len(ms)
            fn = os.path.basename(f)
            if name != 'status 202' or len(ms) < 100:   # 202 太多，只列少数的
                samples = []
                for m in ms[:2]:
                    i = m.start()
                    samples.append(t[max(0, i - 60):i + 80].replace('\n', ' ')[:150])
                print(f'  {fn} x{len(ms)}: {" || ".join(samples)}')
    print(f'  total hits={cnt}')
print('DONE q85')
