# -*- coding: utf-8 -*-
import sys

try:
    import pymysql
    print('pymysql ok')
except Exception as e:
    print('pymysql missing:', e)

try:
    import MySQLdb
    print('mysqldb ok')
except Exception as e:
    print('mysqldb missing:', e)
