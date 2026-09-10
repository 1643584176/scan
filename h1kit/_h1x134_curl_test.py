# -*- coding: utf-8 -*-
"""用 curl.exe 测 api.hackerone.com(绕过 python TLS 指纹差异)"""
import subprocess

TOKEN = "xh/HVu9F69JXKIxyxX1pFdFxV+sdIUcsJxsr4KcxEzs="
args = ["curl", "-s", "-o", r"D:\scan\h1kit\_h1x134_curl_out.txt",
        "-w", "HTTP %{http_code}",
        "-u", "base_alert:" + TOKEN,
        "-H", "Accept: application/json",
        "https://api.hackerone.com/v1/hackers/me"]
p = subprocess.run(args, capture_output=True, text=True, timeout=60)
print("status:", p.stdout)
print("stderr:", p.stderr[:200])
print(open(r"D:\scan\h1kit\_h1x134_curl_out.txt", "r", encoding="utf-8", errors="replace").read()[:400])
