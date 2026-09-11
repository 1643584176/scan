# -*- coding: utf-8 -*-
# g11: commit + push
import subprocess, os
os.chdir(r'D:\scan')

def run(cmd, timeout=600):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    return (r.stdout or '') + (r.stderr or '')

print('== add msg file ==')
print(run('git add .gitcommitmsg.txt').strip()[:200])
print('== commit ==')
c = run('git commit -F .gitcommitmsg.txt')
print(c.strip()[:600])
print('== push ==')
p = run('git push origin dev', timeout=600)
print(p.strip()[:600])
print('== final log ==')
print(run('git log --oneline -3').strip())
print('== status summary ==')
s = run('git status --short')
lines = [l for l in s.split('\n') if l.strip()]
print('remaining change lines:', len(lines))
for l in lines[:10]:
    print('  ' + l)
