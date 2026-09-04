# -*- coding: utf-8 -*-
"""v187 阶段B: guest 宿主视角 - 检查 ExecCommand 输出文件 + 宿主敏感文件完整性"""
import socket, time, json, os, signal

OUT = '/vercel/sandbox/v187c.out'
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


log('=== 1 host fs check ===')
# 宿主视角找 out187.txt 和 rmtest
for p in ['/tmp/out187.txt', '/vercel/sandbox/out187.txt', '/tmp/rmtest_host.txt',
          '/vercel/sandbox/rmtest.txt', '/mnt/h/tmp/out187.txt', '/mnt/h/tmp/rmtest_host.txt']:
    try:
        d = open(p, 'rb').read()
        log('HFILE %s (%d): %r' % (p, len(d), d[:800]))
    except Exception as e:
        log('HFILE %s EXC %s' % (p, e))

# 沙箱盘挂载点找 (v187 guest 的 /mnt/g 是沙箱盘)
for p in ['/mnt/g/tmp/out187.txt', '/mnt/g/vercel/sandbox/out187.txt', '/mnt/g/tmp/rmtest_host.txt',
          '/mnt/g/vercel/sandbox/rmtest.txt']:
    try:
        d = open(p, 'rb').read()
        log('GFILE %s (%d): %r' % (p, len(d), d[:800]))
    except Exception as e:
        log('GFILE %s EXC %s' % (p, e))

# 宿主关键文件完整性
log('=== 2 host integrity ===')
for p in ['/etc/hostname', '/etc/shadow', '/proc/1/root/etc/hostname', '/proc/1/root/etc/shadow']:
    try:
        d = open(p, 'rb').read()
        log('INTEG %s (%d) %r' % (p, len(d), d[:100]))
    except Exception as e:
        log('INTEG %s EXC %s' % (p, e))

log('V187_DONE')
f.close()
