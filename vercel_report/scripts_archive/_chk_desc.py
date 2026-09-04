# -*- coding: utf-8 -*-
"""本地模拟 descriptor 解析逻辑验证 (完整版)"""


def rv(data, off):
    shift = 0
    val = 0
    while off < len(data):
        b = data[off]
        off += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80):
            return val, off
        shift += 7
        if shift > 63:
            return -1, off
    return -1, off


def pstr(s):
    b = s.encode()
    return bytes([0x0a]) + bytes([len(b)]) + b


def pmsg(fno, payload):
    return bytes([(fno << 3) | 2]) + bytes([len(payload)]) + payload


def pvarint(fno, n):
    return bytes([(fno << 3) | 0]) + bytes([n])


def parse_fields(data, off=0):
    out = []
    while off < len(data):
        key, off2 = rv(data, off)
        if key < 0 or off2 > len(data):
            return None
        off = off2
        fno = key >> 3
        wt = key & 7
        if fno == 0:
            return None
        if wt == 0:
            v, off = rv(data, off)
            if v < 0:
                return None
            out.append((fno, wt, v))
        elif wt == 1:
            if off + 8 > len(data):
                return None
            out.append((fno, wt, data[off:off + 8]))
            off += 8
        elif wt == 2:
            ln, off = rv(data, off)
            if ln < 0 or off + ln > len(data):
                return None
            out.append((fno, wt, data[off:off + ln]))
            off += ln
        elif wt == 5:
            if off + 4 > len(data):
                return None
            out.append((fno, wt, data[off:off + 4]))
            off += 4
        else:
            return None
    return out


def parse_file_simple(data):
    flds = parse_fields(data)
    if flds is None:
        return None
    fname = pkg = None
    for fno, wt, v in flds:
        if fno == 1 and wt == 2:
            try:
                fname = v.decode('utf-8')
            except Exception:
                pass
        elif fno == 2 and wt == 2:
            try:
                pkg = v.decode('utf-8')
            except Exception:
                pass
    if fname and fname.endswith('.proto') and pkg:
        return (fname, pkg)
    return None


# 构造 FileDescriptorProto
msg_fields = pstr('process_id') + pvarint(3, 1) + pvarint(4, 1) + pvarint(5, 9)
exec_msg = pstr('ExecRequest') + pmsg(2, msg_fields)
svc = pstr('ContainersService') + pmsg(2, pstr('Exec') + pstr('.ExecRequest') + pstr('.ExecResponse'))
fd = pstr('cell/api/containers/containers.proto') + pstr('vercel.hive.cell.api.containers.v1') + pmsg(4, exec_msg) + pmsg(6, svc)

blob = b'XXXX' * 100 + fd + b'YYYY' * 1000
print('fd len:', len(fd))

fnb = b'containers.proto'
p = blob.find(fnb)
print('found at', p)
kstart = None
for back in range(p, max(0, p - 16), -1):
    if back > 0 and blob[back - 1] == 0x0a:
        ln, off = rv(blob, back)
        if 0 < ln <= 300 and back + ln <= len(blob):
            seg = blob[back:back + ln]
            if seg.endswith(fnb) and seg.count(b'/') <= 8:
                kstart = back - 1
                break
print('kstart:', kstart)

for trial in range(max(0, kstart - 10), kstart + 2):
    r1 = parse_file_simple(blob[trial:])
    r2 = parse_file_simple(blob[trial:trial + 300000])
    print('trial', trial, 'nolimit:', r1, 'limited:', r2)
