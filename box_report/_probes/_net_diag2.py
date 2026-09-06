# -*- coding: utf-8 -*-
"""Check Windows system proxy config & running proxy tools."""
import subprocess
import winreg

print('== Windows system proxy (HKCU Internet Settings) ==')
try:
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                       r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
    for name in ('ProxyEnable', 'ProxyServer', 'ProxyOverride', 'AutoConfigURL'):
        try:
            v, _ = winreg.QueryValueEx(k, name)
            print('  %s = %s' % (name, v))
        except FileNotFoundError:
            print('  %s = (unset)' % name)
    winreg.CloseKey(k)
except Exception as e:
    print('  reg error:', e)

print()
print('== Running proxy-related processes ==')
out = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=20).stdout
kws = ['clash', 'v2ray', 'xray', 'sing-box', 'verge', 'mihomo', 'shadowsocks',
       'ssr', 'trojan', 'naive', 'hysteria', 'nekoray', 'qv2ray', 'proxy']
low = out.lower()
found = False
for kw in kws:
    for ln in low.splitlines():
        if kw in ln and kw != 'proxy':
            print('  ', ln.strip())
            found = True
            break
if not found:
    print('  (no known proxy process running)')

print()
print('== Common install dirs ==')
import os
cands = [
    os.path.expandvars(r'%LOCALAPPDATA%\Clash for Windows'),
    os.path.expandvars(r'%LOCALAPPDATA%\Programs\clash-verge'),
    os.path.expandvars(r'%APPDATA%\clash-verge'),
    os.path.expandvars(r'%APPDATA%\v2rayN'),
    os.path.expandvars(r'%LOCALAPPDATA%\Programs\v2rayN'),
    r'C:\Program Files\Clash for Windows',
    r'C:\Program Files\v2rayN',
]
for c in cands:
    print('  %-45s %s' % (c, 'EXISTS' if os.path.isdir(c) else '-'))
