# -*- coding: utf-8 -*-
# g12: 重推拿完整 push protection 报错
import subprocess, os, io
os.chdir(r'D:\scan')

r = subprocess.run('git push origin dev', shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
full = (r.stdout or '') + (r.stderr or '')
io.open(r'D:\scan\figma_report\_g12_pushfull.txt', 'w', encoding='utf-8').write(full)
print('exit:', r.returncode, 'len:', len(full))
print(full[:4000])
