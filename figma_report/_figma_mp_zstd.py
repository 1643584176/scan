# -*- coding: utf-8 -*-
"""zstd 解压 frame0(应为 Kiwi schema)+ 检查后续帧"""
import zstandard, struct

data = open(r'D:\scan\figma_report\_js\mp_frames.bin', 'rb').read()
pos = 0
frames = []
while pos < len(data):
    ln = struct.unpack('>I', data[pos:pos + 4])[0]
    frames.append(data[pos + 4: pos + 4 + ln])
    pos += 4 + ln

f0 = frames[0]
print('frame0 len:', len(f0), 'magic:', f0[:8], 'ver:', struct.unpack('<I', f0[8:12])[0])
payload = f0[12:]

dctx = zstandard.ZstdDecompressor()
try:
    # 先试直接解压
    r = dctx.decompress(payload)
    print('decompress OK len:', len(r))
except Exception as e:
    print('direct FAIL:', e)
    # 可能是帧格式:前面有额外头(28b52ffd 是 fig-wire 的子协议头?)
    for off in range(4, 24):
        try:
            r = dctx.decompress(payload[off:])
            print('offset %d OK len %d' % (off, len(r)))
            break
        except Exception:
            pass

open(r'D:\scan\figma_report\_js\mp_f0_zstd.bin', 'wb').write(r)
print('saved', len(r))
print('head hex:', r[:64].hex())
asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in r[:300])
print('head asc:', asc[:300])
