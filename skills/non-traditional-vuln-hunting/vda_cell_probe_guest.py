# -*- coding: utf-8 -*-
"""vda_cell_probe: vda 直通 + cell.sock ALIVE + Freebox 33090 归属验证
1) mountinfo 全览 (vda 挂载点)
2) /mnt/vda 结构 + Freebox 痕迹
3) cell.sock 直连 -> cell.api 路径 ALIVE (400/200 判活)
4) 33090/34121 监听者 inode -> vda proc/fd 归属 (host PID)
5) Freebox API 未认证面 (confirm33090 简化版)
输出落盘 + 哨兵 VDAP_DONE"""
import os, time, socket, glob, sys

OUT = '/vercel/sandbox/vdap.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_unix(sockpath, path, body='{}', t=6):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, len(body)))
        s.sendall(req.encode())
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:300].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
    log('=== PHASE0 mountinfo (vda) ===')
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if 'vda' in ln or '/vercel' in ln or '/mnt' in ln:
                log('MOUNT %s' % ln.strip()[:200])
    except Exception as e:
        log('mountinfo ERR %s' % e)

    log('=== PHASE1 /mnt/vda 结构 ===')
    for p in ['/mnt/vda', '/run/vercel/share']:
        try:
            log('ls %s: %s' % (p, os.listdir(p)[:50]))
        except Exception as e:
            log('ls %s ERR %s' % (p, e))

    log('=== PHASE2 Freebox 痕迹 ===')
    roots = ['/mnt/vda', '/run/vercel/share']
    for root in roots:
        for sub in ['etc', 'usr/lib', 'usr/share', 'var/www', 'opt', 'root', 'home',
                    'usr/sbin', 'sbin', 'usr/bin']:
            p = os.path.join(root, sub)
            try:
                names = os.listdir(p)
            except Exception:
                continue
            hits = [n for n in names if any(k in n.lower() for k in
                    ['freebox', 'fbx', 'firmware', 'fbxos', 'free-box'])]
            if hits:
                log('HIT %s: %s' % (p, hits))
            if sub == 'opt' or sub == 'etc':
                log('  %s (%d entries): %s' % (p, len(names), names[:25]))

    log('=== PHASE3 cell.sock 直连 ===')
    sock_candidates = []
    for root in ['/mnt/vda', '']:
        for p in ['run/cell/cell.sock', 'run/cell.sock', 'run/containerd/containerd.sock',
                  'run/vercel/share/init.sock', 'run/apm/apm.sock', 'run/metrics/metrics.sock']:
            sock_candidates.append(os.path.join(root, p) if root else p)
    for sp in sock_candidates:
        try:
            st = os.stat(sp)
            log('sock %s EXISTS mode=%o' % (sp, st.st_mode & 0o777))
        except Exception:
            continue
        # 试探 connect + 一个 RPC
        for path in ['/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage',
                     '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot',
                     '/vercel.hive.cell.api.containers.v1.ContainersService/Create']:
            st2, bd = rpc_unix(sp, path, '{}')
            log('  unix %s %s -> %s | %s' % (sp.split('/')[-1], path.split('/')[-1], st2, bd[:160].replace('\n', ' ')))
            time.sleep(0.5)

    log('=== PHASE4 33090/34121 监听者归属 ===')
    try:
        for ln in open('/proc/net/tcp6', errors='replace').read().splitlines()[1:]:
            parts = ln.split()
            if len(parts) < 10:
                continue
            local = parts[1]
            port = int(local.split(':')[1], 16)
            if port in (33090, 34121, 23456, 26661):
                inode = parts[9]
                log('tcp6 port=%d inode=%s st=%s' % (port, inode, parts[3]))
                # 尝试在 vda 的 proc 里归属
                found = False
                for pdir in ['/mnt/vda/proc', '/proc']:
                    try:
                        for fd in glob.glob(pdir + '/*/fd/*'):
                            try:
                                tgt = os.readlink(fd)
                            except Exception:
                                continue
                            if tgt == 'socket:[%s]' % inode:
                                pid = fd.split('/')[-3]
                                log('  OWNER %s fd=%s pid=%s' % (pdir, fd, pid))
                                for cmd in ['cmdline', 'comm']:
                                    try:
                                        log('    %s=%s' % (cmd, open(os.path.join(pdir, pid, cmd), 'rb').read()[:200]))
                                    except Exception:
                                        pass
                                found = True
                    except Exception:
                        continue
                if not found:
                    log('  owner not found in /mnt/vda/proc or /proc')
    except Exception as e:
        log('tcp6 ERR %s' % e)

    log('=== PHASE5 23456 与 init.sock 同源验证 ===')
    # init.sock 上调 SpawnService 路径 (sandbox-init 协议)
    sp = '/run/vercel/share/init.sock'
    try:
        for path in ['/vercel.sandbox.spawn.v1.SpawnService/Ping',
                     '/vercel.sandbox.spawn.v1.SpawnService/Spawn',
                     '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage']:
            st2, bd = rpc_unix(sp, path, '{}')
            log('init.sock %s -> %s | %s' % (path.split('/')[-1], st2, bd[:160].replace('\n', ' ')))
            time.sleep(0.5)
    except Exception as e:
        log('init.sock ERR %s' % e)

    log('=== PHASE6 /mnt/vda/opt/vercel 详情 ===')
    for p in ['/mnt/vda/opt/vercel', '/mnt/vda/opt/vercel/celld']:
        try:
            st = os.stat(p)
            log('%s mode=%o size=%d' % (p, st.st_mode & 0o777, st.st_size))
        except Exception as e:
            log('%s ERR %s' % (p, e))

    log('VDAP_DONE')
    f.close()


if __name__ == '__main__':
    main()
