"""fig-wire 二进制协议解码器

从 dump 文件解析：每条消息 = 4字节长度 + payload。
payload 格式：'fig-wire' magic(8) + version(1) + session_id(4) + 1字节类型 + protobuf体

输出每类消息的结构树，对比不同身份 dump 找差异字段。
"""
import sys, struct

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read_varint(b, off):
    shift = 0
    val = 0
    while True:
        if off >= len(b):
            return None, off
        c = b[off]
        off += 1
        val |= (c & 0x7F) << shift
        if not (c & 0x80):
            return val, off
        shift += 7


def decode_pb(b, depth=0, max_depth=6):
    """递归解码 protobuf，返回字段列表 [(field, wire, value)]"""
    out = []
    off = 0
    while off < len(b):
        tag, off = read_varint(b, off)
        if tag is None:
            break
        field = tag >> 3
        wire = tag & 7
        if field == 0:
            break
        if wire == 0:  # varint
            val, off = read_varint(b, off)
            out.append((field, wire, val))
        elif wire == 1:  # 64-bit
            if off + 8 > len(b):
                break
            val = b[off:off+8]
            off += 8
            out.append((field, wire, val.hex()))
        elif wire == 2:  # length-delimited
            ln, off = read_varint(b, off)
            if ln is None or off + ln > len(b):
                break
            val = b[off:off+ln]
            off += ln
            # 尝试判断是字符串还是嵌套消息
            try:
                s = val.decode("utf-8")
                if all(32 <= ord(ch) < 127 or ch in "\n\t" for ch in s):
                    out.append((field, wire, "str:" + s))
                else:
                    raise ValueError
            except Exception:
                if depth < max_depth:
                    try:
                        sub = decode_pb(val, depth + 1, max_depth)
                        out.append((field, wire, ("msg[" + ", ".join(f"{f}:{v}" if not isinstance(v, str) or len(str(v)) < 40 else f"{f}:{str(v)[:40]}..." for f, w, v in sub) + "]")))
                    except Exception:
                        out.append((field, wire, "bytes:" + val[:24].hex()))
                else:
                    out.append((field, wire, "bytes:" + val[:24].hex()))
        elif wire == 5:  # 32-bit
            if off + 4 > len(b):
                break
            out.append((field, wire, b[off:off+4].hex()))
            off += 4
        else:
            break
    return out


def parse_messages(fn):
    data = open(fn, "rb").read()
    off = 0
    msgs = []
    while off + 4 <= len(data):
        ln = struct.unpack(">I", data[off:off+4])[0]
        off += 4
        if off + ln > len(data):
            break
        msgs.append(data[off:off+ln])
        off += ln
    return msgs


def analyze(fn, label):
    print(f"\n{'='*60}\n{label}: {fn}\n{'='*60}")
    msgs = parse_messages(fn)
    for i, m in enumerate(msgs):
        if m[:8] == b"fig-wire":
            print(f"  [{i}] len={len(m)} FIG-WIRE握手(首条, type 0xb5)")
            continue
        # 裸格式: 28b52ffd(4) + type(1) + body
        if len(m) < 5 or m[:4] != bytes.fromhex("28b52ffd"):
            print(f"  [{i}] 未知格式: {m[:40].hex()}")
            continue
        mtype = m[4]
        body = m[5:]
        print(f"  [{i}] len={len(m)} type=0x{mtype:02x}")
        try:
            fields = decode_pb(body)
            for f, w, v in fields:
                s = str(v)
                if s.startswith("str:"):
                    print(f"      f{f} str: {s[4:]}")
                elif s.startswith("msg"):
                    print(f"      f{f} {s[:300]}")
                else:
                    print(f"      f{f} (w{w}): {s[:120]}")
        except Exception as e:
            print(f"      decode err {e}")
            print(f"      raw: {body[:120].hex()}")


if __name__ == "__main__":
    analyze("mp_1666382703778278399_dump.bin", "基准 user-id=自己")
    analyze("mp_1484993095538571712_dump.bin", "冒充A user-id=目标用户")
