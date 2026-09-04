# -*- coding: utf-8 -*-
"""解析 fig-wire 帧:尝试解压 frame0 + 分析小帧结构"""
import zlib, gzip, brotli, struct, json

data = open(r'D:\scan\figma_report\_js\mp_frames.bin', 'rb').read()
pos = 0
frames = []
while pos < len(data):
    ln = struct.unpack('>I', data[pos:pos + 4])[0]
    frames.append(data[pos + 4: pos + 4 + ln])
    pos += 4 + ln
print('frames:', len(frames))

# ---- frame 0: 尝试解压 ----
f0 = frames[0]
print('\nframe0 len:', len(f0), 'head:', f0[:12].hex())
payload = f0[12:]  # fig-wire\x01\x00\x00\x00 + 4 字节?
print('payload head:', payload[:16].hex())
for name, fn in [
    ('zlib', lambda b: zlib.decompress(b)),
    ('gzip', lambda b: gzip.decompress(b)),
    ('brotli', lambda b: brotli.decompress(b)),
    ('zlib-auto', lambda b: zlib.decompress(b, -15)),
    ('zlib-raw', lambda b: zlib.decompress(b, wbits=-zlib.MAX_WBITS)),
]:
    try:
        r = fn(payload)
        print('[%s] OK len=%d head=%s' % (name, len(r), r[:60].hex()))
        asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in r[:200])
        print('   asc:', asc[:200])
        open(r'D:\scan\figma_report\_js\mp_f0_%s.bin' % name, 'wb').write(r)
    except Exception as e:
        print('[%s] FAIL %s' % (name, str(e)[:60]))

# ---- 小帧结构 ----
print('\n=== 小帧 ===')
for i, f in enumerate(frames[1:], 1):
    print('frame%d len=%d: %s' % (i, len(f), f[:40].hex()))
    asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in f[:80])
    print('   ', asc)
