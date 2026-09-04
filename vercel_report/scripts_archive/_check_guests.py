# -*- coding: utf-8 -*-
"""检查各 guest 脚本的输出文件/完成标志 + 全盘搜 J546 捕获"""
import os, re

D = r'F:\scan\skills\non-traditional-vuln-hunting'
targets = ['guest_udp.py', 'guest_udp2.py', 'guest_fast.py', 'pid1_scan.py',
           'host_probe_guest3.py', 'guest_vsock_probe.py', 'guest_vsock_probe2.py',
           'guest_vsock_check.py', 'celld_probe_guest.py', 'hp2_run.py']
for t in targets:
    p = os.path.join(D, t)
    if not os.path.exists(p):
        print('MISSING:', t)
        continue
    txt = open(p, encoding='utf-8', errors='replace').read()
    out_m = re.findall(r"OUT\s*=\s*'([^']+)'", txt)
    done_m = re.findall(r"([A-Z_]+_DONE)", txt)
    net = re.findall(r'network|deny-all|allow-all', txt, re.I)
    print('%-22s OUT=%s DONE=%s' % (t, out_m[:2], done_m[:2]))

print()
print('=== 全盘搜 cap/resp base64 文件 ===')
for dirpath, dirnames, filenames in os.walk(r'F:\scan'):
    if '__pycache__' in dirpath or '.venv' in dirpath or '.git' in dirpath:
        continue
    for f in filenames:
        if re.search(r'cap\d|resp\d|j54[456]|spawnreq|spawnresp|killresp', f, re.I):
            print(' ', os.path.join(dirpath, f), os.path.getsize(os.path.join(dirpath, f)))
