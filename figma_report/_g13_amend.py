# -*- coding: utf-8 -*-
# g13: 移除 _r54_anon_recv.txt + amend + 重推
import subprocess, os
os.chdir(r'D:\scan')

def run(cmd, timeout=600):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    return (r.stdout or '') + (r.stderr or '')

print('== rm --cached ==')
print(run('git rm --cached figma_report/_r54_anon_recv.txt').strip()[:300])
print('== add gitignore ==')
print(run('git add .gitignore').strip()[:200])
print('== amend ==')
print(run('git commit --amend --no-edit').strip()[:400])
print('== push ==')
p = run('git push origin dev', timeout=600)
print(p.strip()[:3000])
print('== final ==')
print(run('git log --oneline -3').strip())
print(run('git status --short').strip()[:300])
