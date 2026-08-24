# 本地反汇编 main.run 找 [rsp+0x448]/[rsp+0x450] 槽赋值 -> base64公钥来源
import re
from capstone import *

# 提取 RUN_HEX
data = open(r"D:\scan\exp_j204_out.txt", "r", encoding="utf-8", errors="replace").read()
m = re.search(r"RUN_HEX ([0-9a-f]+)", data)
hexs = m.group(1)
code = bytes.fromhex(hexs)
print("code len", len(code))

BASE = 0x86ec40
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = False

lines = []
for ins in md.disasm(code, BASE):
    lines.append((ins.address, ins.mnemonic, ins.op_str))

# 1) 找 [rsp+0x448] 和 [rsp+0x450] 的所有写入点
print("\n=== writes to [rsp+0x448]/[rsp+0x450] ===")
for a, mn, op in lines:
    if ("0x448" in op or "0x450" in op) and ("mov" in mn or "lea" in mn or "xor" in mn):
        print(hex(a), mn, op)

# 2) 找 call 0x83abc0 附近 30 条指令
print("\n=== around call 0x83abc0 (0x86f0b7) ===")
for i, (a, mn, op) in enumerate(lines):
    if a == 0x86f0b7:
        for j in range(max(0, i - 25), min(len(lines), i + 20)):
            aa, mm, oo = lines[j]
            mark = " <<<" if j == i else ""
            print(hex(aa), mm, oo, mark)

# 3) 找 main.run 里的 lea [rip+...] 立即数地址 (字符串引用)
print("\n=== all lea r??, [rip+disp] in main.run (potential strings) ===")
for a, mn, op in lines:
    mm = re.match(r"r[a-z0-9]+, \[rip \+ (0x[0-9a-f]+)\]", op)
    if mm and mn == "lea":
        target = a + 7 + int(mm.group(1), 16)
        print(hex(a), mn, op, "->", hex(target))
