# -*- coding: utf-8 -*-
"""scan_neigh: 100.64.0.0/16 邻居网段探测 (只读)
PHASE0 ARP/邻居表 + fib_trie
PHASE1 扫 3 个 /24 (自己段/scanl4段/网关段) 关键端口
PHASE2 开放端口 HTTP banner
PHASE3 邻居 PTR
输出落盘 + 哨兵 SCAN_NEIGH_DONE"""
import os, time, socket, select

OUT = '/vercel/sandbox/scanneigh.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def self_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('100.64.0.1', 53))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def tcp_scan_batch(ip, ports, timeout=0.25):
    open_ports = []
    pend = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        try:
            s.connect_ex((ip, p))
        except Exception:
            s.close()
            continue
        pend.append((p, s))
    deadline = time.time() + timeout
    while pend and time.time() < deadline:
        try:
            _, w, _ = select.select([], [s for _, s in pend], [], 0.05)
        except Exception:
            break
        if not w:
            continue
        wset = set(id(s) for s in w)
        remaining = []
        for p, s in pend:
            if id(s) in wset:
                err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err == 0:
                    open_ports.append(p)
                s.close()
            else:
                remaining.append((p, s))
        pend = remaining
    for p, s in pend:
        s.close()
    return sorted(open_ports)


def http_probe(ip, port, timeout=2):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 300:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:300]
    except Exception as e:
        return ('ERR %s' % e).encode()[:100]


def main():
    ip = self_ip() or '100.64.186.165'
    log('self ip: %s' % ip)
    self_last = int(ip.split('.')[-1])
    self_third = int(ip.split('.')[2])
    self_prefix = '100.64.%d' % self_third

    log('=== PHASE0 ARP/邻居 ===')
    try:
        for p in ['/proc/net/arp', '/proc/net/neigh']:
            if os.path.exists(p):
                with open(p, 'r') as fh:
                    for ln in fh.readlines():
                        log('%s: %s' % (p, ln.strip()[:150]))
    except Exception as e:
        log('arp ERR %s' % e)
    try:
        import subprocess
        for cmd in [['ip', 'neigh'], ['ip', 'addr'], ['arp', '-a']]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                log('%s -> %s' % (' '.join(cmd), (r.stdout or r.stderr)[:800]))
            except Exception as e:
                log('%s ERR %s' % (' '.join(cmd), e))
    except Exception as e:
        log('subproc ERR %s' % e)

    log('=== PHASE1 网段关键端口扫描 ===')
    ports = [22, 53, 80, 443, 23456, 3000, 3306, 5432, 6379, 8080, 8443, 9000,
             33090, 34121, 2379, 10250, 6443]
    # 目标: 自己/24 全部 + 网关段 0/24
    targets = []
    for i in range(1, 255):
        if i == self_last:
            continue
        targets.append('%s.%d' % (self_prefix, i))
    for i in range(1, 255):
        targets.append('100.64.0.%d' % i)
    hits = {}
    t0 = time.time()
    done = 0
    for ip in targets:
        o = tcp_scan_batch(ip, ports)
        if o:
            hits[ip] = o
            log('HIT %s open=%s' % (ip, o))
        done += 1
        if done % 100 == 0:
            log('progress %d/%d elapsed=%.0fs' % (done, len(targets), time.time() - t0))
    log('scan done elapsed=%.0fs hits=%d' % (time.time() - t0, len(hits)))

    log('=== PHASE2 banner ===')
    for ip, ps in sorted(hits.items()):
        for p in ps:
            r = http_probe(ip, p)
            log('banner %s:%d -> %r' % (ip, p, r))

    log('=== PHASE3 PTR ===')
    for ip in sorted(hits.keys()):
        try:
            log('PTR %s -> %s' % (ip, socket.gethostbyaddr(ip)[0]))
        except Exception as e:
            log('PTR %s ERR %s' % (ip, e))

    log('SCAN_NEIGH_DONE')
    f.close()


if __name__ == '__main__':
    main()
