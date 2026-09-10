# -*- coding: utf-8 -*-
"""诊断 740:当前是否 elevated + chrome 兼容性标志(2026-09-09)"""
import io, sys, ctypes, winreg

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 1. 当前是否 elevated
h = ctypes.windll.shell32.IsUserAnAdmin()
print("IsUserAnAdmin:", bool(h))

# 2. chrome 兼容性标志(当前用户)
paths = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"),
]
for hive, key in paths:
    try:
        k = winreg.OpenKey(hive, key)
        i = 0
        while True:
            try:
                name, val, _ = winreg.EnumValue(k, i)
                if "chrome" in name.lower():
                    print(f"{hive} {name} = {val}")
                i += 1
            except OSError:
                break
        winreg.CloseKey(k)
    except OSError as e:
        print(f"{hive} open err {e}")
