# -*- coding: utf-8 -*-
"""解析 pidfd_run15.log: v13 变体验证
- 'out' 注入 -> API 输出 FAKEHOST-xxx
- 'exit7' 注入 -> exitCode 7
- 'hang' 注入 -> 命令挂起/超时
- POOL-INJECT -> 连接池注入记录
- SEND -> accept 注入记录"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run15.log', encoding='utf-8', errors='replace').read()

print("=== trigger 响应 (含 FAKEHOST/POOLINJ/exitCode/超时) ===")
for m in re.finditer(r'trig (\d+\.\d) (\w+): (\d+) ({.*?})\n', raw):
    body = m.group(4)
    t = ''
    ms = re.search(r'"startedAt":(\d+)', body)
    if ms:
        t = 'ts=%d' % (int(ms.group(1)) // 1000)
    print('trig %s %s: %d %s' % (m.group(1), m.group(2), int(m.group(3)), t))

print("\n=== stdout 数据行 ===")
for m in re.finditer(r'\{"data":"([^"]*)\\n"', raw):
    d = m.group(1)
    if any(k in d for k in ['FAKEHOST', 'POOLINJ', 'hostname', 'done', 'PID', 'root']):
        print('data: %r' % d[:120])

print("\n=== 完成行 (exitCode/durationMs) ===")
for m in re.finditer(r'\{"command":\{.*?"exitCode":(\d+),"durationMs":(\d+)\}\}\n', raw):
    print('exit=%s dur=%sms' % (m.group(1), m.group(2)))

print("\n=== guest 侧注入记录 ===")
for pat in ['ACCEPT srcfd=9 -> fd=', 'SEND ', 'POST-SEND', 'POOL-INJECT', 'LISTEN THREAD', 'POOL INJECT done', 'PHASE3 done', 'ACCEPTED fd=']:
    for m in re.finditer(re.escape(pat), raw):
        i = m.start()
        print(raw[i:i+240].replace('\n', ' ')[:240])
    print('---')

print("\n=== 超时/异常 ===")
for pat in ['timeout', 'Timeout', '500', 'exitCode":7', 'FAKEHOST', 'POOLINJ']:
    cnt = raw.count(pat)
    print('%s: %d 处' % (pat, cnt))
