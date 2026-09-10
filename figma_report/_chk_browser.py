# -*- coding: utf-8 -*-
"""检查本地浏览器自动化环境"""
import sys, io, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import importlib.util as u

print('== python modules ==')
for m in ['playwright', 'selenium', 'pyppeteer', 'nodriver', 'requests', 'httpx',
          'websocket', 'websockets', 'undetected_chromedriver']:
    print(f'  {m}: {bool(u.find_spec(m))}')

print('== browsers ==')
cands = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
]
for c in cands:
    print(f'  {c}: {os.path.exists(c)}')

print('== drivers ==')
for d in ['chromedriver', 'msedgedriver']:
    hits = glob.glob(rf'C:\**\{d}*.exe', recursive=False)
    print(f'  {d}: {hits[:3]}')
    # PATH 里找
    import shutil
    p = shutil.which(d)
    print(f'  which {d}: {p}')
