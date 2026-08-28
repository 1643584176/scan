# -*- coding: utf-8 -*-
"""获取 dnslog.cn 子域(本地),用于验证 DNS 隧道闭环"""
import urllib.request, urllib.parse

req = urllib.request.Request("http://www.dnslog.cn/getdomain.php")
req.add_header("User-Agent", "Mozilla/5.0")
with urllib.request.urlopen(req, timeout=15) as r:
    d = r.read().decode().strip()
print("DOMAIN:", d)
