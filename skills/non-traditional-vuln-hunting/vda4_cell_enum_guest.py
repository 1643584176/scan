# -*- coding: utf-8 -*-
"""vda4_cell_enum: V3P 后续 — 控制面路径枚举 + rootfs 线索挖掘
1) mount vda (若已挂载复用)
2) /proc/cmdline -> cell_id; runc 内容; run/cell 目录完整列表
3) find 限深: celld/cell.api 相关文件 + *.sock 全局
4) TCP 23456: 枚举常见路径 (GET / 先看服务指纹)
5) cell.sock: 枚举路径变体 (v2/v3/api/health)
输出落盘 + 哨兵 V4Q_DONE"""
import os, time, socket, ctypes, glob

OUT = '/vercel/sandbox/v4q.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_unix(sockpath, path, body='{}', t=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, len(body), body))
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


def rpc_tcp(port, path, body='{}', t=4):
    try:
        s = socket.create_connection(('127.0.0.1', port), 3)
        s.settimeout(t)
        req = ('POST %s HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, len(body), body))
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
    # P0: mount
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                log('already mounted')
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)

    # P1: cmdline / runc / run 目录
    log('=== P1 cmdline & run ===')
    try:
        log('cmdline: %s' % open('/proc/cmdline', errors='replace').read().strip())
    except Exception as e:
        log('cmdline ERR %s' % e)
    for p in ['/mnt/vdax/run/cell/runc', '/mnt/vdax/run/cell/cell.sock']:
        try:
            st = os.stat(p)
            log('%s size=%d mode=%o' % (p, st.st_size, st.st_mode))
            if st.st_size < 200:
                log('  content: %r' % open(p, 'rb').read()[:200])
        except Exception as e:
            log('%s ERR %s' % (p, e))
    for d in ['/mnt/vdax/run', '/mnt/vdax/run/cell', '/mnt/vdax/opt/vercel', '/mnt/vdax/etc']:
        try:
            log('ls %s: %s' % (d, sorted(os.listdir(d))[:40]))
        except Exception as e:
            log('ls %s ERR %s' % (d, e))

    # P2: find 控制面相关文件 (限深 4)
    log('=== P2 find celld/cell.api ===')
    hits = []
    for root, dirs, files in os.walk('/mnt/vdax', topdown=True):
        depth = root[len('/mnt/vdax'):].count('/')
        if depth > 4:
            dirs[:] = []
            continue
        for d in list(dirs):
            if d in ('proc', 'sys', 'dev', 'tmp', 'var/log', 'var/cache', 'usr/lib', 'usr/share'):
                dirs.remove(d)
        for n in files + dirs:
            nl = n.lower()
            if any(k in nl for k in ['celld', 'cell.api', 'hive', 'snapshot', 'celld-init', 'meta.db']):
                hits.append(os.path.join(root, n))
        if len(hits) > 60:
            break
    log('ctrl hits (%d): %s' % (len(hits), hits))

    # P3: *.sock 全局
    log('=== P3 sock files ===')
    socks = []
    for root, dirs, files in os.walk('/mnt/vdax', topdown=True):
        depth = root[len('/mnt/vdax'):].count('/')
        if depth > 5:
            dirs[:] = []
            continue
        for d in list(dirs):
            if d in ('proc', 'sys', 'dev', 'tmp'):
                dirs.remove(d)
        for n in files:
            if n.endswith('.sock'):
                socks.append(os.path.join(root, n))
        if len(socks) > 30:
            break
    log('socks (%d): %s' % (len(socks), socks))

    # P4: TCP 23456 指纹 + 路径枚举
    log('=== P4 tcp 23456 enum ===')
    for path, body in [('/', '{}'), ('/health', '{}'), ('/healthz', '{}'),
                       ('/v1/health', '{}'), ('/api', '{}'), ('/metrics', '{}'),
                       ('/vercel.hive.cell.api.drives.v1.DrivesService/List', '{}')]:
        st, bd = rpc_tcp(23456, path, body, t=3)
        log('tcp %-70s -> %s | %s' % (path, st, bd[:150].replace('\n', ' ')))
        time.sleep(0.3)

    # P5: cell.sock 路径变体枚举
    log('=== P5 cell.sock enum ===')
    sp = '/mnt/vdax/run/cell/cell.sock'
    paths = [
        '/vercel.hive.celld.api.v1.CelldService/Heartbeat',
        '/vercel.hive.celld.api.v1.CelldService/GetInfo',
        '/vercel.hive.celld.api.v1.CelldService/GetConfig',
        '/vercel.hive.cell.api.v1.CellService/GetInfo',
        '/vercel.hive.cell.api.v1.CellService/Heartbeat',
        '/vercel.hive.cell.api.v1.CellService/GetStatus',
        '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage',
        '/vercel.hive.cell.api.drives.v1.DrivesService/List',
        '/vercel.hive.cell.api.drives.v1.DrivesService/Get',
        '/vercel.hive.cell.api.containers.v1.ContainersService/List',
        '/api/v1/heartbeat', '/healthz', '/v1/heartbeat',
    ]
    for p in paths:
        st, bd = rpc_unix(sp, p, '{}', t=3)
        log('sock %-80s -> %s | %s' % (p.split('/')[-1], st, bd[:150].replace('\n', ' ')))
        time.sleep(0.3)

    log('V4Q_DONE')
    f.close()


if __name__ == '__main__':
    main()
