# -*- coding: utf-8 -*-
"""提取 v115-v118 所有 StreamOutput 相关错误"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
for fname in ('_run_v115_out.txt', '_run_v116_out.txt', '_run_v117_out.txt', '_run_v118_out.txt'):
    txt = io.open(fname, encoding='utf-8', errors='replace').read()
    print('=' * 20, fname)
    for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
        d = m.group(1).encode().decode('unicode_escape', errors='replace')
        for l in d.splitlines():
            s = l.strip()
            if any(k in s for k in ('unmarshal', 'invalid character', 'promised', 'FRAME', 'STREAM', 'compressed',
                                    'protocol error', 'raw message', 'part', 'FLAG')):
                print('  ', s[:500])
