# -*- encoding:UTF-8 -*-
import os
import sys

work_dir = os.path.abspath(os.path.dirname(sys.argv[0]))


server_IP = '10.101.70.236'
server_port = 81

login_url = "/scp-usermgmtcomponent/admin/login?username=test&password=dGVzdA=="


u'''小区平台UAT数据库'''
PostgreSQL = {
    "host": "10.101.70.238",
    "user": "hdsc_postgres",
    "password": "hdsc_postgres",
    "db": "hdsc_db",
    "port": "5432"
}

replay_files = ['refuse.gor']
record_dir = 'records' + os.path.sep
result_dir = 'result' + os.path.sep
white_list_dir = 'white_list' + os.path.sep
fitter_dir = 'fitters' + os.path.sep


# 巡更应用
patrol_para_name = u'路飞'
patrol_plan_name = 'autotest'
