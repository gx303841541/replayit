# -*- encoding:UTF-8 -*-
import os
import sys

work_dir = os.path.abspath(os.path.dirname(sys.argv[0]))


server_IP = '192.168.0.94'
server_port = 81

server_IP2 = '192.168.0.86'
server_port2 = 9046

login_url = "/scp-usermgmtcomponent/admin/login?username=test&password=dGVzdA=="


u'''小区平台UAT数据库'''
PostgreSQL = {
    "host": "192.168.0.238",
    "user": "hdsc_postgres",
    "password": "hdsc_postgres",
    "db": "hdsc_db",
    "port": "5432"
}
