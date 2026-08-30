# -*- coding: utf-8 -*-
"""chk23456: 确认 guest 内监听 23456 的进程归属 + 真实网络拓扑
1) UDP getsockname 法确认真实源 IP (大端 vs 小端)
2) /proc/net/route 打印路由
3) tcp6 表 inode -> /proc/*/fd 找监听 23456 的进程
4) 连接测试 127.0.0.1/自己IP/网关 的 23456
输出落盘 + 哨兵 CHK23456_DONE"""
import os, time, socket

OUT = '/vercel/sandbox/chk23456.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def try_conn(ip, port, timeout=2):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return True
    except Exception as e:
        return str(e)[:80]


def main():
    log('=== CHK23456 PHASE0 UDP getsockname ===')
    for dst in ['100.64.0.1', '1.1.1.1', '8.8.8.8']:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect((dst, 53))
            log('udp connect %s:53 -> src %s' % (dst, s.getsockname()))
            s.close()
        except Exception as e:
            log('udp %s ERR %s' % (dst, e))

    log('=== CHK23456 PHASE1 /proc/net/route ===')
    try:
        with open('/proc/net/route', 'r') as fh:
            for ln in fh.readlines():
                log('ROUTE: %s' % ln.strip())
    except Exception as e:
        log('route ERR %s' % e)

    log('=== CHK23456 PHASE2 tcp6 原始行 ===')
    listen_inodes = {}
    try:
        with open('/proc/net/tcp6', 'r') as fh:
            lines = fh.readlines()
        for ln in lines[1:]:
            parts = ln.split()
            if len(parts) >= 10:
                st = parts[3]
                inode = parts[9]
                uid = parts[7]
                laddr = parts[1]
                lport = int(laddr.split(':')[-1], 16)
                log('TCP6: %s st=%s uid=%s inode=%s' % (laddr, st, uid, inode))
                if st == '0A':
                    listen_inodes[inode] = laddr
    except Exception as e:
        log('tcp6 ERR %s' % e)

    log('=== CHK23456 PHASE3 进程归属 (inode -> /proc/*/fd) ===')
    for inode, laddr in listen_inodes.items():
        found = []
        try:
            pids = [p for p in os.listdir('/proc') if p.isdigit()]
        except Exception as e:
            log('listdir ERR %s' % e)
            pids = []
        for pid in pids:
            try:
                fd_dir = '/proc/%s/fd' % pid
                for fd in os.listdir(fd_dir):
                    try:
                        tgt = os.readlink(os.path.join(fd_dir, fd))
                        if 'socket:[%s]' % inode in tgt:
                            # 进程信息
                            try:
                                with open('/proc/%s/comm' % pid) as cf:
                                    comm = cf.read().strip()
                            except Exception:
                                comm = '?'
                            try:
                                with open('/proc/%s/cmdline' % pid) as cf:
                                    cmdline = cf.read().replace('\x00', ' ').strip()
                            except Exception:
                                cmdline = '?'
                            try:
                                with open('/proc/%s/status' % pid) as cf:
                                    status = cf.read()
                                uids = [l for l in status.splitlines() if l.startswith('Uid:')]
                            except Exception:
                                uids = ['?']
                            found.append((pid, comm, cmdline[:120], uids))
                    except Exception:
                        pass
            except Exception:
                pass
        log('listen %s inode=%s -> %s' % (laddr, inode, found))

    log('=== CHK23456 PHASE4 连接测试 ===')
    self_ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('100.64.0.1', 53))
        self_ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    cands = ['127.0.0.1', '::1'] + self_ips + ['100.64.0.1', '88.185.64.100', '151.36.64.100']
    for ip in cands:
        r = try_conn(ip, 23456)
        log('conn %s:23456 -> %s' % (ip, r))
        time.sleep(0.2)

    log('=== CHK23456 PHASE5 23456 服务指纹 (只读) ===')
    try:
        s = socket.create_connection(('127.0.0.1', 23456), timeout=3)
        s.settimeout(3)
        s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 2000:
                    break
        except socket.timeout:
            pass
        s.close()
        log('23456 GET / -> %r' % data[:1000])
    except Exception as e:
        log('23456 ERR %s' % e)

    log('CHK23456_DONE')
    f.close()


if __name__ == '__main__':
    main()
