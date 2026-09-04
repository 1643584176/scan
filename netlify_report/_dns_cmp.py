# -*- coding: utf-8 -*-
"""对比关键域名解析"""
import socket

for h in ['app.netlify.com', 'api.netlify.com', 'int-api.netlify.com', 'functions.internal.netlify.com',
          '*.netlify.app', 'sec-b-08v4pk.netlify.app']:
    try:
        ips = sorted(set(socket.gethostbyname_ex(h)[2]))
        print('%-40s %s' % (h, ips[:6]))
    except Exception as e:
        print('%-40s FAIL %s' % (h, str(e)[:60]))
