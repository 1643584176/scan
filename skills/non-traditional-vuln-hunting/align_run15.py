# -*- coding: utf-8 -*-
"""精确对齐 run15 每个 trigger 的完成情况"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run15.log', encoding='utf-8', errors='replace').read()
starts = [(m.start(), m.group(1), int(m.group(2))) for m in re.finditer(r'trig (\d+\.\d) \w+: 200 .*?"startedAt":(\d+)', raw)]
for i, (pos, tag, ts) in enumerate(starts):
    end = starts[i+1][0] if i+1 < len(starts) else pos + 8000
    seg = raw[pos:end]
    dur = re.search(r'"durationMs":(\d+)', seg)
    exitc = re.search(r'"exitCode":(\d+)', seg)
    outs = re.findall(r'"data":"([^"]{0,60})', seg)
    o = outs[0][:40] if outs else ''
    print('%-6s ts=%d dur=%-5s exit=%-3s out=%r' % (tag, ts//1000,
          dur.group(1) if dur else 'PEND', exitc.group(1) if exitc else '-', o))
