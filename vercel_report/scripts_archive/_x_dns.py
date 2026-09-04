# -*- coding: utf-8 -*-
"""DNS 测试"""
import socket
try:
    print(socket.gethostbyname('sb-1jngq0bhfvia.vercel.run'))
except Exception as e:
    print('ERR', e)
