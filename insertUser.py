#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20161005
# @version: 1.0.0.1009
import argparse
import base64
import copy
import json
import logging
import os
import random
import re
import sys
import time

import requests

from basic.cprint import cprint
from basic.log_tool import MyLogger


class ArgHandle():
    def __init__(self):
        self.parser = self.build_option_parser("-" * 50)

    def build_option_parser(self, description):
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            '-c', '--count',
            dest='count',
            action='store',
            default=1,
            type=int,
            help='Specify how many times to replay',
        )
        parser.add_argument(
            '-p', '--server-port',
            dest='server_port',
            action='store',
            default=81,
            type=int,
            help='Specify TCP server port, default is 20001',
        )
        parser.add_argument(
            '-i', '--server-IP',
            dest='server_IP',
            action='store',
            default='10.101.70.236',
            help='Specify TCP server IP address',
        )
        return parser

    def get_args(self, attrname):
        return getattr(self.args, attrname)

    def check_args(self):
        pass

    def run(self):
        self.args = self.parser.parse_args()
        cprint.notice_p("CMD line: " + str(self.args))
        self.check_args()


def convert_to_dictstr(src):
    if isinstance(src, dict):
        return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    elif isinstance(src, str):
        return json.dumps(json.loads(src), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    elif isinstance(src, bytes):
        return json.dumps(json.loads(src.decode('utf-8')), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    elif isinstance(src, list):
        src = {'Fuck': src}
        return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    else:
        LOG.error('Unknow type(%s): %s' % (src, str(type(src))))
        return None


def update_token():
    global token
    print('update_token')
    url = "http://%s:%d/%s" % (arg_handle.get_args('server_IP'),
                               arg_handle.get_args('server_port'), "/scp-usermgmtcomponent/admin/login?username=test&password=dGVzdA==")
    print(url)
    header = {
        "FrontType": 'scp-admin-ui',
    }
    resp = requests.get(url, headers=header)
    try:
        token = resp.json()['data']['token']
        print("Get token: " + token)
    except Exception as e:
        print('get token fail![%s]' % (str(e)))


def send(url, method, payload):
    headers = {}
    if method == 'POST':
        headers["Authorization"] = token
        headers = {
            "FrontType": 'egc-mobile-ui',
            "Content-Type": 'application/json',
            "Authorization": token,
        }
        LOG.info('POST url: ' + url)
        # LOG.yinfo('head: ' + convert_to_dictstr(headers))
        #LOG.info('bodys: ' + json.dumps(payload))
        try:
            r = requests.post(url, data=json.dumps(payload),
                              headers=headers, timeout=10)
            LOG.warn('status_code: ' + str(r.status_code))
            try:
                LOG.warn('resp: ' + convert_to_dictstr(r.json()))
            except json.decoder.JSONDecodeError:
                LOG.warn('resp: ' + r.text)
        except Exception as e:
            LOG.error('error: ' + str(e))

    if method == 'GET':
        headers["Authorization"] = token
        headers = {
            "FrontType": 'egc-mobile-ui',
            "Content-Type": 'application/json',
            "Authorization": token,
        }
        LOG.info('GET url: ' + url)
        # LOG.yinfo('head: ' + convert_to_dictstr(headers))
        LOG.info('bodys: ' + json.dumps(payload))
        try:
            r = requests.get(url, data=payload,
                             headers=headers, timeout=10, **attrs)
            try:
                LOG.warn('resp: ' + convert_to_dictstr(r.json()))
            except json.decoder.JSONDecodeError:
                LOG.warn('resp: ' + r.text)
        except Exception as e:
            LOG.error('error: ' + str(e))

    try:
        return (r.status_code, r.json(), r.headers)
    except json.decoder.JSONDecodeError:
        return (r.status_code, r.text, r.headers)
    except:
        return (400, {}, {})


if __name__ == "__main__":
    global LOG
    global cprint
    global arg_handle
    cprint = cprint()
    arg_handle = ArgHandle()
    arg_handle.run()

    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace(
        'py', 'log'), clevel=logging.DEBUG, fenable=False)
    picpath = "pics"
    if not os.path.exists(picpath):
        LOG.error('no pics dir!!!')
        sys.exit()

    msg = {
        "name": "小狗狗test",
        "userType": "1",
        "sex": "1",
        "idenType": "111",
        "birth": "",
        "idenNum": "211223198708080088",
        "nation": "1",
        "origin": "阿富汗",
        "phone": "18888888888",
        "email": "",
        "company": "",
        "dept": "",
        "station": "",
        "focusOnPersonnel": "0",
        "houseName": "锦绣江南1期11栋2单元201",
        "description": "",
        "houseUuid": "9e16dfa21ffb4d499214a3af01df1d97",
        "houseUuidBeforeModify": "",
        "userUuid": "",
        "fileName": "",
        "facePicBase64": "/static/img/default_picture.5c0a75e.png",
        "fingerCode1": "",
        "oldFingerCode1": "",
        "uuid": '',
        "orgParentUuid": 852
    }

    # fingerCodes
    fingerCode_list = [
        "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"
    ]

    # get all pics
    all_pics = os.listdir(picpath)
    random.shuffle(all_pics)
    i = 0
    rs = []
    for pic in all_pics * 10:
        if i >= arg_handle.get_args('count'):
            break
        LOG.debug('create info for pic: %s' % pic)
        r = copy.deepcopy(msg)
        with open(picpath + os.path.sep + pic, "rb") as f:
            pic_str = base64.b64encode(f.read()).decode('utf-8')
        pic_type = 'jpeg'
        id = '%04d' % i
        r["name"] = "小狗狗" + id
        r["idenNum"] = "21122319850606" + id
        r["phone"] = "1888885" + id
        r["fileName"] = r["name"] + '.jpg'
        r["facePicBase64"] = "data:image/" + \
            pic_type + ';base64,' + pic_str
        r["fingerCode1"] = fingerCode_list[random.randint(
            0, len(fingerCode_list) - 1)]
        i += 1
        rs.append(r)
        LOG.warn('name: %s, picname: %s, fingerCode1: %s' %
                 (r["name"], pic, r["fingerCode1"]))

    update_token()
    for r in rs:
        LOG.info('Insert user: %s' % r["name"])
        send(url='http://%s:%s/scp-mdmapp/user/insertUser' % (arg_handle.get_args('server_IP'), arg_handle.get_args('server_port')),
             method='POST', payload=r)
        time.sleep(0.05)
