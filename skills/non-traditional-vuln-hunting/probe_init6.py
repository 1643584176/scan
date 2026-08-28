# -*- coding: utf-8 -*-
"""沙箱内解析 sandbox-init 的 protobuf FileDescriptorProto
手写 wire format 解析: 提取 spawnv1 全部消息字段(含 SpawnResponse)"""
import base64, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import cmd, fresh_sandbox

ANALYZER = r'''
import struct

data = open('/vercel/sandbox/init.bin','rb').read()

def rd_varint(b, i):
    r = 0; s = 0
    while True:
        x = b[i]; i += 1
        r |= (x & 0x7f) << s
        if not (x & 0x80):
            return r, i
        s += 7

def fields(b, i, end):
    """yield (field_no, wire_type, start, payload_end)"""
    while i < end:
        tag, i = rd_varint(b, i)
        fno = tag >> 3; wt = tag & 7
        if fno == 0:
            break
        if wt == 0:
            _, i = rd_varint(b, i)
        elif wt == 1:
            i += 8
        elif wt == 2:
            ln, i = rd_varint(b, i)
            yield fno, wt, i, i + ln
            i += ln
        elif wt == 5:
            i += 4
        else:
            break

def parse_msg(b, i, end):
    """返回 {fno: [(start,end),...]}"""
    out = {}
    for fno, wt, s, e in fields(b, i, end):
        out.setdefault(fno, []).append((s, e))
    return out

# 找 package 字符串 "vercel.sandbox.spawn.v1" 附近: package field = 2 (tag 0x12)
PKG = b'vercel.sandbox.spawn.v1'
hits = []
pos = 0
while True:
    pos = data.find(PKG, pos)
    if pos < 0:
        break
    hits.append(pos)
    pos += 1
print('pkg hits:', len(hits))

# 对每个命中: 回退找 fd 起点(往前搜索 0x22 = field4 message_type 的 tag 结构)
# 简单策略: 取命中位置前 200KB 到命中后 200KB, 暴力扫描所有可能起点解析 FileDescriptorProto
best = None
for p in hits:
    for start in range(max(0, p - 300000), p):
        # 起点特征: field1(name) 为 string, 内容含 .proto; 且 field2(package)=vercel.sandbox.spawn.v1
        if data[start] != 0x0a:
            continue
        ln = data[start+1]
        if ln < 5 or ln > 80:
            continue
        name = data[start+2:start+2+ln]
        if not name.endswith(b'.proto'):
            continue
        # 检查 package 字段
        i = start + 2 + ln
        if data[i] != 0x12:
            continue
        ln2 = data[i+1]
        if data[i+2:i+2+ln2] != PKG:
            continue
        # 找 message_type 字段(0x22), 从 i+2+ln2 开始解析若干消息
        msgs = []
        j = i + 2 + ln2
        # 解析整段(fd 长度未知, 用贪婪: 一直解析到乱)
        total = len(data) - j
        for fno, wt, s, e in fields(data, j, min(j + 400000, len(data))):
            if fno == 4 and wt == 2:  # message_type
                m = parse_msg(data, s, e)
                mname = b''
                for fno2, lst in m.items():
                    if fno2 == 1:
                        mname = data[lst[0][0]:lst[0][1]]
                        break
                msgs.append((mname, m, s, e))
        if len(msgs) >= 2:
            best = (start, name, msgs)
            break
    if best:
        break

if not best:
    print('NO DESCRIPTOR FOUND')
    sys.exit(0)

start, fname, msgs = best
print('file:', fname.decode())
print('messages:', len(msgs))
for mname, m, ms, me in msgs:
    print('=== message %s ===' % mname.decode(errors='replace'))
    for fno, lst in m.items():
        if fno != 1:
            for s, e in lst:
                raw = data[s:e]
                print('  field %d: %s' % (fno, raw[:120].hex()))
                print('           %r' % raw[:120])
'''

sid = fresh_sandbox("exp_init2")
print("sid:", sid)
time.sleep(2)

c, r = cmd(sid, "bash", ["-c", "cp /run/vercel/share/sandbox-init /vercel/sandbox/init.bin 2>&1; echo ok"], timeout_ms=30000)
print("cp:", c, r[:200])

payload = base64.b64encode(ANALYZER.encode()).decode()
inject = "import base64;open('/vercel/sandbox/analyze2.py','wb').write(base64.b64decode('%s'))" % payload
c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
print("inject:", c, r[:150])

c, r = cmd(sid, "python3", ["/vercel/sandbox/analyze2.py"], timeout_ms=180000)
print("=== analyze2 ===")
print(r[:6000])
