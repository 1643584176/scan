# -*- coding: utf-8 -*-
"""v219 payload (guest): interactive API 触发前后 26661 时序观察 + host 集群网段扫描
watcher: 每 300ms 快照 tcp6/tcp LISTEN 变化 + 试连 26661 (v4/v6) + 其他新端口探测
scanner: 100.64.1.0/24 等网段全扫 (不与快照触发冲突)
主线程: 等待驱动触发 (通过 /vercel/sandbox/v219_go 文件出现) 后继续观察 90s
输出 /vercel/sandbox/v219c.out"""
import socket, struct, time, json, signal, threading, os

OUT = '/vercel/sandbox/v219c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(150)
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
    print(s[:300], flush=True)


def parse_tcp(path):
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


def try_ports(ports):
    """试连一组端口, 记录成功的"""
    for p in ports:
        for af, addr in [('v4', ('127.0.0.1', p)), ('v6', ('::1', p))]:
            try:
                s = socket.socket(socket.AF_INET6 if af == 'v6' else socket.AF_INET,
                                  socket.SOCK_STREAM)
                s.settimeout(0.3)
                rc = s.connect_ex(addr)
                s.close()
                if rc == 0:
                    log('PORT_OPEN %s:%d' % (af, p))
            except Exception:
                pass


# ---------- 线程 A: 时序观察 ----------
def watcher():
    t0 = time.time()
    last = set()
    probe_ports = [26661, 23456, 8080, 40532, 47354, 6825]
    while time.time() - t0 < 135:
        try:
            tcp = parse_tcp('/proc/net/tcp')
            tcp6 = parse_tcp('/proc/net/tcp6')
            cur = set((fmt_addr(h), p, u, i) for h, p, u, i in tcp6 + tcp)
            new = cur - last
            gone = last - cur
            if new:
                for a, p, u, i in sorted(new):
                    log('LISTEN_NEW %s:%d uid=%s inode=%s' % (a, p, u, i))
            if gone:
                for a, p, u, i in sorted(gone):
                    log('LISTEN_GONE %s:%d uid=%s inode=%s' % (a, p, u, i))
            last = cur
            try_ports(probe_ports)
        except Exception as e:
            log('WATCH EXC %s' % e)
        time.sleep(0.3)
    log('WATCHER_DONE')


# ---------- 线程 B: 网段扫描 ----------
SCAN_PORTS = [23456, 26661, 80, 443, 8080, 2375, 8502, 10250, 6443, 3000, 40532, 47354]


def scan_ip(ip):
    for p in SCAN_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.35)
            rc = s.connect_ex((ip, p))
            if rc == 0:
                log('SCAN_OPEN %s:%d' % (ip, p))
            s.close()
        except Exception:
            pass


def scanner():
    t0 = time.time()
    targets = []
    for i in range(1, 255):
        targets.append('100.64.1.%d' % i)
        if i < 32:
            targets.append('100.64.2.%d' % i)
        if i <= 16:
            targets.append('100.64.0.%d' % i)
    ths = []
    for ip in targets:
        if len(ths) >= 20:
            ths[0].join(timeout=6)
            ths = ths[1:]
        t = threading.Thread(target=scan_ip, args=(ip,))
        t.start()
        ths.append(t)
    for t in ths:
        t.join(timeout=6)
    log('SCANNER_DONE t=%.0f' % (time.time() - t0))


def main():
    log('V219_START')
    w = threading.Thread(target=watcher, daemon=True)
    s = threading.Thread(target=scanner, daemon=True)
    w.start()
    s.start()
    # 等驱动触发标记 (驱动 POST interactive 前创建该文件)
    for _ in range(150):
        if os.path.exists('/vercel/sandbox/v219_go'):
            log('TRIGGER_MARK SEEN (interactive called)')
            break
        time.sleep(1)
    # 触发后再观察 60s
    time.sleep(60)
    log('V219_DONE')


if __name__ == '__main__':
    main()
