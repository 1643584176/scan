# -*- coding: utf-8 -*-
"""本地解析目标 IP(供 deny-all 沙箱内 IP 直连使用)"""
import socket

for h in ['webhook.site', 'httpbin.org', '1.1.1.1', '8.8.8.8', 'example.com']:
    try:
        print(h, socket.gethostbyname(h))
    except Exception as e:
        print(h, 'ERR', e)
