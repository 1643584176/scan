# -*- coding: utf-8 -*-
# q86: 环境检查——cookies 内容（有无 aws-waf-token）+ 浏览器自动化可用性
import sys, io, os, subprocess, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print('===== cookie 文件 =====')
for f in glob.glob(r'D:\scan\figma_report\_waf_cookies*.txt') + glob.glob(r'D:\scan\figma_report\_*cookies*.txt'):
    try:
        t = io.open(f, encoding='utf-8', errors='replace').read().strip()
        names = [c.split('=')[0].strip() for c in t.split(';') if '=' in c]
        print(os.path.basename(f), f'({len(t)} bytes)')
        print('   cookies:', names)
    except Exception as e:
        print(f, 'ERR', e)

print('\n===== python 包 =====')
out = subprocess.run([r'D:\scan\.venv\Scripts\python.exe', '-m', 'pip', 'list'],
                     capture_output=True, text=True, encoding='utf-8', errors='replace')
for line in (out.stdout or '').splitlines():
    low = line.lower()
    if any(k in low for k in ('playwright', 'selenium', 'pyppeteer', 'requests', 'curl', 'execjs', 'js2py')):
        print('  ', line.strip())

print('\n===== node 环境 =====')
out = subprocess.run(['node', '--version'], capture_output=True, text=True)
print('  node:', (out.stdout or '').strip() or out.stderr.strip())
for pkg in ('puppeteer', 'playwright', 'playwright-core'):
    out = subprocess.run(['npm', 'ls', '-g', pkg, '--depth=0'], capture_output=True, text=True, shell=True)
    s = (out.stdout or '') + (out.stderr or '')
    ok = pkg in s and 'empty' not in s
    print(f'  npm -g {pkg}: {"YES" if ok else "no"}')

print('\n===== 本地浏览器 =====')
cands = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
]
for c in cands:
    print('  ', c, os.path.exists(c))
print('DONE q86')
