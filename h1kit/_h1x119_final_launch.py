# -*- coding: utf-8 -*-
"""移除 RUNASADMIN → 杀 Chrome → 普通权限无痕+调试启动(2026-09-09)"""
import winreg, ctypes, subprocess, time, io, sys, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LAYERS = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"

# 1. 删 RUNASADMIN
try:
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, LAYERS, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
    try:
        val, _ = winreg.QueryValueEx(k, CHROME)
        print("before:", val)
        winreg.DeleteValue(k, CHROME)
        print("RUNASADMIN removed")
    except FileNotFoundError:
        print("key already clean")
    winreg.CloseKey(k)
except OSError as e:
    print("registry err:", e)

# 2. elevated 杀残留(一次 UAC)
ps1 = r"D:\scan\h1kit\_h1x114_relaunch.ps1"  # 该文件现只用于杀进程(启动部分下面自己来)
kill_ps1 = r"D:\scan\h1kit\_h1x119_kill.ps1"
with open(kill_ps1, "w") as f:
    f.write("Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue\n")
cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File \"{kill_ps1}\""
res = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell", cmd, None, 0)
print("kill ShellExecuteW ret:", res)
time.sleep(6)

def chrome_count():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
        "(Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True, timeout=30).stdout.strip()
    try:
        return int(out)
    except Exception:
        return -1

print("chrome procs after kill:", chrome_count())

# 3. 普通权限启动(标志已删,无需 UAC)
subprocess.Popen([CHROME, "--incognito", "--remote-debugging-port=9222", "https://hackerone.com"],
                 creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                 close_fds=True)
print("chrome launched (normal priv, incognito)")

def cdp_alive():
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2) as r:
            return r.read().decode()[:150]
    except Exception:
        return None

for i in range(60):
    time.sleep(1)
    v = cdp_alive()
    if v:
        print("CDP ALIVE:", v)
        break
    if i % 5 == 0:
        print(f"  waiting t+{i}s")
else:
    print("CDP NOT UP after 60s")
