# -*- coding: utf-8 -*-
"""查看 host_probe_guest3/guest_udp2/pid1_scan/hp2_run 的结束标记与用途"""
import os, re

D = r'F:\scan\skills\non-traditional-vuln-hunting'
for t in ['host_probe_guest3.py', 'guest_udp2.py', 'pid1_scan.py', 'hp2_run.py', 'guest_fast.py']:
    p = os.path.join(D, t)
    txt = open(p, encoding='utf-8', errors='replace').read()
    print('=' * 20, t)
    # 头部 docstring
    m = re.match(r'"""(.*?)"""', txt, re.S)
    if m:
        print('DOC:', m.group(1).strip()[:300])
    # 结束标记类字符串
    for mm in re.finditer(r"'([A-Z][A-Z0-9_]{3,}_DONE)'|\"([A-Z][A-Z0-9_]{3,}_DONE)\"", txt):
        print('  marker:', mm.group(0))
    # 最后 8 行
    lines = [l for l in txt.splitlines() if l.strip()]
    print('  last:')
    for l in lines[-6:]:
        print('   ', l[:120])
