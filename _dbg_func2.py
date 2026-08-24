# -*- coding: utf-8 -*-
"""调试: _func 结构 dump (dataoff 相对 0 基准 = 文件偏移?)"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100

# dataoff[0] = 0x13478 -> _func 位置? 试 文件偏移 0x13478
F = 0x13478
raw = d[F:F+64]
print("raw @0x13478:", raw.hex())
for i in range(0, 32, 4):
    v = struct.unpack("<I", raw[i:i+4])[0]
    print(f"  +{i:#04x}: {v:#010x} ({v})")

# 试 0x13478 - 8 (可能前面有别的)
for off in (0x13470, 0x13478, 0x13480, 0x13488):
    raw = d[off:off+24]
    print(f"\n@{off:#x}: {raw.hex()}")

# funcnametab 起始 0x60 -> PC+0x60 = 0x5ab160 检查内容
print("\nfuncnametab head:", d[PC+0x60:PC+0x100])
