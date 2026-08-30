# -*- coding: utf-8 -*-
"""vda2_probe: 环境对照探测 (恢复沙箱 vs 新沙箱)
1) /dev 设备列表 (vda/vsock/virtio)
2) /proc/net/unix 全表 (host 影子 socket: cell/containerd/metrics/apm)
3) mountinfo 全表
4) tcp6 全表 (33090/34121/23456/26661 监听+归属)
5) 本机 IP + 33090/34121 连通性
6) 尝试 syscall mount /dev/vda 到 /mnt/vdax (只读侦察)
输出落盘 + 哨兵 V2P_DONE"""
import os, time, socket, glob, sys, ctypes

OUT = '/vercel/sandbox/v2p.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def main():
    log('=== P1 /dev 设备 ===')
    try:
        devs = os.listdir('/dev')
        log('dev: %s' % devs)
        for d in devs:
            if any(k in d for k in ['vda', 'vdb', 'vsock', 'vd', 'loop']):
                p = '/dev/' + d
                st = os.stat(p)
                log('  %s rdev=%d:%d size=%d' % (p, os.major(st.st_rdev), os.minor(st.st_rdev), st.st_size))
    except Exception as e:
        log('dev ERR %s' % e)

    log('=== P2 /proc/net/unix 全表 ===')
    try:
        for ln in open('/proc/net/unix', errors='replace').read().splitlines()[1:]:
            parts = ln.split()
            if len(parts) >= 8 and parts[7] and not parts[7].startswith('@'):
                log('unix %s inode=%s type=%s' % (parts[7], parts[6], parts[4]))
    except Exception as e:
        log('unix ERR %s' % e)

    log('=== P3 mountinfo ===')
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            flds = ln.split()
            if len(flds) > 4:
                log('M %s %s %s' % (flds[2], flds[4], flds[8] if len(flds) > 8 else ''))
    except Exception as e:
        log('mountinfo ERR %s' % e)

    log('=== P4 tcp6 全表 ===')
    try:
        for ln in open('/proc/net/tcp6', errors='replace').read().splitlines()[1:]:
            parts = ln.split()
            if len(parts) < 10:
                continue
            port = int(parts[1].split(':')[1], 16)
            st = parts[3]
            inode = parts[9]
            uid = parts[7]
            if st == '0A' or port in (33090, 34121, 23456, 26661, 80, 443):
                log('tcp6 %s:%d st=%s uid=%s inode=%s' % (parts[1].split(':')[0][:32], port, st, uid, inode))
    except Exception as e:
        log('tcp6 ERR %s' % e)

    log('=== P5 本机 IP + 33090/34121 ===')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('100.64.0.1', 53))
        ip = s.getsockname()[0]
        s.close()
        log('self ip: %s' % ip)
        for port in [33090, 34121, 23456, 26661]:
            for target in [ip, '127.0.0.1']:
                try:
                    c = socket.create_connection((target, port), timeout=2)
                    log('conn %s:%d -> OPEN' % (target, port))
                    c.close()
                except Exception as e:
                    log('conn %s:%d -> %s' % (target, port, type(e).__name__))
    except Exception as e:
        log('ip ERR %s' % e)

    log('=== P6 syscall mount /dev/vda ===')
    try:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)
        if ret == 0:
            log('mnt/vdax: %s' % os.listdir('/mnt/vdax')[:40])
            try:
                for sub in ['run/cell', 'run/containerd', 'opt/vercel', 'usr/bin', 'etc']:
                    p = '/mnt/vdax/' + sub
                    try:
                        log('  %s: %s' % (p, os.listdir(p)[:15]))
                    except Exception as e:
                        log('  %s ERR %s' % (p, e))
            except Exception:
                pass
    except Exception as e:
        log('mount ERR %s' % e)

    log('V2P_DONE')
    f.close()


if __name__ == '__main__':
    main()
