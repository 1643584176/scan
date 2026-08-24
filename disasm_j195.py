# 本地反汇编: verify(0x83b3a0) + wrapunary(0x83aea0) + newverifier(0x83abc0) + main_main(0x86ea80)
# 从 exp_j195_marker.txt 提取HEX, capstone反汇编
import re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

data = open("exp_j195_marker.txt", encoding="utf-8", errors="replace").read()
data = data.replace("\\n", "\n")

funcs = {}
cur = None
for line in data.splitlines():
    line = line.strip()
    if line.startswith("FUNC"):
        parts = line.split()
        cur = parts[1]
        funcs[cur] = {"vaddr": int(parts[2], 16), "size": int(parts[3]), "hex": ""}
    elif line.startswith("HEX") and cur:
        funcs[cur]["hex"] = line.split(" ", 1)[1]

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

for name, info in funcs.items():
    code = bytes.fromhex(info["hex"])
    print(f"\n{'='*70}\n{name} @ {hex(info['vaddr'])} size={info['size']} ({len(code)}B)\n{'='*70}")
    for i in md.disasm(code, info["vaddr"]):
        print(f"  {i.address:#x}: {i.mnemonic:8s} {i.op_str}")
