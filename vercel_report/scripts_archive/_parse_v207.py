# -*- coding: utf-8 -*-
"""解析 v207 输出: 提取 PROXY/REPLAY-raw/REPLAY-mod 响应, 解 connect frames + gzip -> 明文"""
import re, zlib

p = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\9aa693e0\e2ed552c.txt'
d = open(p, encoding='utf-8', errors='replace').read()


def unescape_b(s):
    """把 b'...' repr 还原为字节"""
    out = b''
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n == 'x' and i + 3 < len(s):
                out += bytes([int(s[i + 2:i + 4], 16)])
                i += 4
            elif n == '\\':
                out += b'\\'
                i += 2
            elif n == 'n':
                out += b'\n'
                i += 2
            elif n == 'r':
                out += b'\r'
                i += 2
            elif n == 't':
                out += b'\t'
                i += 2
            else:
                out += bytes([ord(n)])
                i += 2
        else:
            out += c.encode('latin-1')
            i += 1
    return out


def parse_frames(dec):
    """connect envelope 帧: [1 flags][3 len][payload], payload 每帧 gzip"""
    out = []
    pos = 0
    while pos + 4 <= len(dec):
        flags = dec[pos]
        ln = int.from_bytes(dec[pos + 1:pos + 4], 'big')
        payload = dec[pos + 4:pos + 4 + ln]
        out.append((flags, payload))
        pos += 4 + ln
    return out


# 提取所有 PROXY/REPLAY 行
pat = re.compile(r"\[(\d+\.\d+)\]\s+((?:PROXY resp|REPLAY-raw|REPLAY-mod) \d+ dec \d+): b'(.*?)'")
for m in pat.finditer(d):
    ts, kind, raw = m.groups()
    dec = unescape_b(raw)
    # 只处理 dec 含 gzip 帧的
    print('== %s @%s dec=%d' % (kind, ts, len(dec)))
    frames = parse_frames(dec)
    for fi, (flags, payload) in enumerate(frames):
        txt = ''
        try:
            txt = zlib.decompress(payload, 16 + 15).decode('utf-8', errors='replace')
        except Exception as e:
            txt = 'DECOMPRESS-EXC'
            try:
                txt = repr(zlib.decompress(payload, 16 + 15))
            except Exception:
                pass
        print('  frame%d flags=0x%x len=%d: %r' % (fi, flags, len(payload), txt[:300]))
    print()
