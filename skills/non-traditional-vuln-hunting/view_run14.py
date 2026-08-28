# -*- coding: utf-8 -*-
"""解析 pidfd_run14.log: trigger 时间线 + guest ACCEPT/SEND 对齐
关键判别: 伪造 SpawnEvent 流被 host 接受 -> trigger 无真实输出 + durationMs 极小"""
import re, sys, json
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run14.log', encoding='utf-8', errors='replace').read()

print("=== trigger 时间线 ===")
for m in re.finditer(r'trig (\d+\.\d) (\w+): 200 .*?"startedAt":(\d+).*?durationMs":(\d+).*?"exitCode":([^,}]*).*?}', raw):
    print('trig %s %s started=%s dur=%sms exit=%s' % (m.group(1), m.group(2),
          int(m.group(3))//1000, m.group(4), m.group(5)))
for m in re.finditer(r'burst (\d+\.\d) (\w+): 200 .*?"startedAt":(\d+).*?durationMs":(\d+).*?"exitCode":([^,}]*).*?}', raw):
    print('burst %s %s started=%s dur=%sms exit=%s' % (m.group(1), m.group(2),
          int(m.group(3))//1000, m.group(4), m.group(5)))

print("\n=== guest ACCEPT/SEND (X-Timestamp 对齐) ===")
for m in re.finditer(r'ACCEPT srcfd=9 -> fd=(\d+) mode=(\w+).*?X-Timestamp: (\d+)', raw):
    print('ACCEPT fd=%s mode=%s ts=%s' % (m.group(1), m.group(2), m.group(3)))
for pat in ['ACCEPT srcfd=9 -> errno', 'ACCEPTED fd=', 'SEND ', 'POST-SEND', 'LISTEN THREAD', 'PHASE3 done']:
    for m in re.finditer(re.escape(pat), raw):
        i = m.start()
        print(raw[i:i+260].replace('\n', ' ')[:260])
    print('---')

# 统计异常 trigger: durationMs 极小(<50) 但无真实输出的(伪造可能被接受)
print("\n=== 可疑伪造命中(非 echo 类且 dur<50ms) ===")
for m in re.finditer(r'(?:trig|burst) (\d+\.\d) (\w+): 200 .*?"startedAt":(\d+).*?durationMs":(\d+).*?"exitCode":([^,}]*).*?}', raw):
    if m.group(4) not in ('0', '1', '2', '3', '4', '5'):
        print('%s %s dur=%sms exit=%s' % (m.group(1), m.group(2), m.group(4), m.group(5)))
