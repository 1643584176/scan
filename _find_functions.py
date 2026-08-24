# -*- coding: utf-8 -*-
"""本地: functab 反查 verifierInterceptor 函数地址
方法:
1. 找 "verifierInterceptor" 在 gopclntab 内所有出现 (funcnametab 候选)
2. 遍历 dataoff -> _func{entryOff u32, nameOff i32, ...}
3. nameOff 与 F 的关系: F - nameOff = funcnametab_start (应恒定)
4. 命中 -> vaddr = textStart + entryOff
"""
import struct

d = open("_sandbox_init_new.bin", "rb").read()
PC = 0x5ab100      # .gopclntab 文件偏移
PC_SIZE = 0x2a0508

# 1) 找目标字符串出现位置
targets = [b"verifierInterceptor", b"checkSignature", b"NewVerifierFromBase64",
           b"(devel)", b"go1.25"]
for t in targets:
    pos = 0
    hits = []
    while True:
        i = d.find(t, pos)
        if i < 0 or len(hits) >= 10:
            break
        hits.append(i)
        pos = i + 1
    print(f"STR {t.decode()} @", [hex(h) for h in hits])

# 2) 反查 functab: 遍历 pclntab 内所有可能 dataoff
# _func 结构: entryOff(4) nameOff(4) args(4) ...
# 假设 funcnametab_start 未知, 用众数法
from collections import Counter
stats = Counter()
hits_detail = []
PC_END = PC + PC_SIZE
for foff in range(PC, PC_END - 32, 4):  # 4 字节对齐扫描
    entryoff = struct.unpack("<I", d[foff:foff+4])[0]
    nameoff = struct.unpack("<i", d[foff+4:foff+8])[0]
    if nameoff <= 0 or nameoff > 0x200000:
        continue
    if entryoff > 0x700000:  # text 大小约 0x406ed1
        continue
    # 校验 _func 合理: pcsp/pcfile/pcln 也在合理范围
    pcsp = struct.unpack("<i", d[foff+12:foff+16])[0]
    pcln = struct.unpack("<i", d[foff+20:foff+24])[0]
    if pcsp < 0 or pcsp > 0x300000 or pcln < 0 or pcln > 0x300000:
        continue
    # nameoff 指向的字符串应可读 (含 \x00 终止)
    naddr = foff + nameoff  # 相对当前?? 不对, 相对 funcnametab_start
    # 用众数: funcnametab_start = F - nameoff
    for F in [i for t in targets for i in [] if False] or []:
        pass
    stats[nameoff] += 1

# 3) 对每个目标字符串 F, 找 nameoff = F - fs, fs 未知
# 但 nameoff 是 int32 且 funcnametab 在 pclntab 内 -> fs in [PC, PC+0x1000]
# 对 fs in range: 找所有 _func 使 nameoff == F - fs, 且 entryoff 合理
found_funcs = {}
for F in []:
    pass

# 简化: 对每个扫描到的 _func, 直接尝试所有目标字符串偏移
# 若存在 fs 使 F - nameoff 相同 -> 命中
samples = []  # (foff, entryoff, nameoff)
for foff in range(PC, PC_END - 32, 4):
    entryoff = struct.unpack("<I", d[foff:foff+4])[0]
    nameoff = struct.unpack("<i", d[foff+4:foff+8])[0]
    if nameoff <= 0 or nameoff > 0x200000 or entryoff > 0x700000:
        continue
    pcsp = struct.unpack("<i", d[foff+12:foff+16])[0]
    pcln = struct.unpack("<i", d[foff+20:foff+24])[0]
    if pcsp < 0 or pcsp > 0x300000 or pcln < 0 or pcln > 0x300000:
        continue
    samples.append((foff, entryoff, nameoff))
print(f"\nsamples: {len(samples)}")

# 对每个目标字符串 F: nameoff = F - funcnametab_start
# funcnametab_start 未知 -> 用所有样本的 (F - nameoff) 众数
for F in [0x5ddc68, 0x62361c]:  # checkSignature / NewVerifierFromBase64 (j257 位置)
    c = Counter()
    for _, _, nameoff in samples:
        c[F - nameoff] += 1
    top = c.most_common(5)
    print(f"\nF={hex(F)}: top funcnametab_start candidates:", [(hex(k), v) for k, v in top])
    if top:
        fs = top[0][0]
        for foff, entryoff, nameoff in samples:
            if F - nameoff == fs:
                # 读完整名字
                naddr = fs + nameoff
                end = d.find(b"\x00", naddr)
                nm = d[naddr:end].decode(errors="replace")
                print(f"  FUNC {nm[:100]} entryoff={hex(entryoff)} vaddr={hex(0x401000+entryoff)} _func@{hex(foff)}")
