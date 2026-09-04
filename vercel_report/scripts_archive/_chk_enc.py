# -*- coding: utf-8 -*-
"""本地验证 any_spec 编码是否含非法 UTF-8"""
import json, struct, sys
sys.stdout.reconfigure(encoding='utf-8')


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


def pbool(field_no, v):
    return pvarint((field_no << 3)) + (b'\x01' if v else b'\x00')


proc = {"user": {"uid": 0, "gid": 0},
        "args": ["/bin/true"],
        "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
        "cwd": "/", "terminal": False}
any_spec = pstr(1, 'types.containerd.io/opencontainers/runtime-spec/1/Spec') + pstr(2, json.dumps(proc).encode())
print('any_spec len =', len(any_spec))
bad = [b for b in any_spec if b > 0x7F]
print('non-ascii bytes:', bad)

# 构造 T1 请求
CID = 'v41pwn'
EXID = 'ex41a'
t1 = pstr(1, CID) + pstr(7, EXID) + pmsg(3, any_spec)
print('T1 len =', len(t1))
bad2 = [b for b in t1 if b > 0x7F]
print('T1 non-ascii:', bad2)

# 手动检查 UTF-8 合法性
def utf8_ok(bs):
    try:
        bs.decode('utf-8')
        return True
    except Exception as e:
        return False

print('any_spec utf8 ok:', utf8_ok(any_spec))
print('t1 utf8 ok:', utf8_ok(t1))

# 检查长度字段是否正确
import struct as st
i = 0
while i < len(any_spec):
    tag = any_spec[i]
    fno = tag >> 3
    wire = tag & 7
    i += 1
    # varint length
    ln = 0
    shift = 0
    while True:
        b = any_spec[i]
        i += 1
        ln |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    val = any_spec[i:i+ln]
    i += ln
    print('field %d wire %d len %d ascii=%s' % (fno, wire, ln, all(x < 0x80 for x in val)))

# 打印 JSON 部分确认
j = json.dumps(proc)
print('json repr:', j[:120])
