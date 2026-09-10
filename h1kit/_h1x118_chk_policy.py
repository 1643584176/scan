# -*- coding: utf-8 -*-
"""查 Chrome 企业策略(RemoteDebuggingAllowed 等)(2026-09-09)"""
import io, sys, winreg

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

paths = [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Google\Policies\Chrome"),
    (winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome"),
]
for hive, key in paths:
    try:
        k = winreg.OpenKey(hive, key)
        i = 0
        found = []
        while True:
            try:
                name, val, _ = winreg.EnumValue(k, i)
                found.append(f"{name}={val}")
                i += 1
            except OSError:
                break
        winreg.CloseKey(k)
        if found:
            print(f"[{key}]")
            for f in found:
                print("   ", f)
        else:
            print(f"[{key}] (empty)")
    except OSError:
        print(f"[{key}] not exist")
