from capstone import Cs, CS_ARCH_X86, CS_MODE_64
md = Cs(CS_ARCH_X86, CS_MODE_64)
print("capstone OK")
i = list(md.disasm(bytes.fromhex("48896c24f0488d6c24f0"), 0x571700))[0]
print(i.mnemonic, i.op_str)
