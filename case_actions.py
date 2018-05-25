#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""case tool
   by Kobe Gong. 2018-4-4
"""

import datetime
import json
import os
import random
import re
import shutil
import sys
import threading
import time

import psycopg2
import requests

import APIs.common_APIs as common_APIs
from case_config import config
from case_tools.case_checker import Checker

APIs_list = [
    'update_token',
    'update_config_from_DB',
    'update_config_from_resp',
    'update_config_by_random',
    'config_dumps',
]


class APIs(Checker):
    def update_token(self):
        self.LOG.info('update_token')
        url = "http://%s:%d/%s" % (config.server_IP,
                                   config.server_port, config.login_url)
        self.LOG.debug(url)
        header = {
            "FrontType": 'scp-admin-ui',
        }
        resp = requests.get(url, headers=header)
        try:
            token = resp.json()['data']['token']
            config.token = token
            self.LOG.debug("Get token: " + token)
        except Exception as e:
            self.LOG.error('get token fail![%s]' % (str(e)))

    def cloud_update_token(self):
        self.LOG.info('cloud_update_token')
        url = "http://%s:%d/%s" % (config.cloud_server_IP,
                                   config.cloud_server_port, config.cloud_login_url)
        self.LOG.debug(url)
        header = {
            "FrontType": 'egc-admin-ui',
        }
        resp = requests.post(url, headers=header)
        try:
            token = resp.json()['data']['token']
            config.token = token
            self.LOG.debug("Get token: " + token)
        except Exception as e:
            self.LOG.error('get token fail![%s]' % (str(e)))

    def update_config_from_DB(self, table, whichone, item_list):
        resp = self.DB_sql_send(table, whichone)
        #self.LOG.debug("get from DB: " + str(resp))
        for id, key in item_list:
            self.LOG.debug('set config.%s = "%s"' % (key, resp[id]))
            setattr(config, key, resp[id])

    def update_config_from_resp(self, *args):
        for k, v in args:
            self.LOG.debug('set config.%s = "%s"' % (k, v))
            setattr(config, k, v)

    def update_config_by_randomstr(self, *args):
        for k, v in args:
            self.LOG.debug('set config.%s = "%s"' %
                           (k, common_APIs.random_str(v)))
            setattr(config, k, common_APIs.random_str(v))

    def config_dumps(self):
        config_dict = {}
        for item in dir(config):
            if item.startswith('_') or (type(config.__dict__[item]) == type(os)):
                continue
            config_dict[item] = config.__dict__[item]
            #self.LOG.warn('%s: %s' % (item, config.__dict__[item]))
        self.LOG.info(self.convert_to_dictstr(config_dict))


class Action(APIs):
    def do_setup(self, datas_dict):
        self._init_()
        if 'setup' in datas_dict:
            self.LOG.info('setup start...')
            for action in datas_dict['setup']:
                if action.endswith(')'):
                    self.LOG.info("run: %s" % ("self.%s" % (action)))
                    eval(str(self.data_wash("self.%s" % (action))))
                else:
                    self.LOG.info("run: %s" % ("self.%s()" % (action)))
                    eval(str(self.data_wash("self.%s()" % (action))))
            self.LOG.info('setup end.\n\n')
        else:
            self.LOG.error('"setup" config error, please check it!')
            assert False

    def do_run(self, datas_dict):
        if 'steps' in datas_dict:
            step_id = 0
            for step in datas_dict['steps']:
                step_id += 1
                if 'name' in step:
                    step_name = step["name"]
                else:
                    step_name = str(step_id)
                self.LOG.info('step %s start...' % (step_name))
                resp = self.send_data(
                    step['mode'], self.data_wash(step['send']))
                self.resp = resp
                self.result_check(self.data_wash(step['check']), resp)
                self.action(step['action'])
                self.LOG.info(
                    'step %s end.\n%s\n\n' % (step_name, '-' * 20))
            self.case_pass()
        else:
            self.LOG.error('"setup" config error, please check it!')
            assert False

    def do_teardown(self, datas_dict):
        if 'teardown' in datas_dict:
            self.LOG.info('teardown start...')
            for action in datas_dict['teardown']:
                if action.endswith(')'):
                    eval("self.%s" % (action))
                else:
                    eval("self.%s()" % (action))
            self.LOG.info('teardown end.')
        else:
            self.LOG.error('"teardown" config error, please check it!')
            assert False

    def send_data(self, mode, data):
        resp = ''
        if mode['protocol'][0] == 'http':
            header = {
                "FrontType": 'egc-mobile-ui',
                "Content-Type": 'application/json',
                "Authorization": config.token,
            }
            if mode['url'].startswith('http'):
                url = mode['url']
            else:
                url = "http://%s:%d/%s" % (config.server_IP,
                                           config.server_port, mode['url'])
            self.LOG.debug(url)
            #self.LOG.debug("send headers: " + self.convert_to_dictstr(header))
            self.LOG.debug("send msg: " + self.convert_to_dictstr(data))
            if mode['protocol'][1] == "get":
                try:
                    resp = requests.get(url, headers=header, timeout=1)
                except requests.exceptions.ConnectTimeout:
                    self.LOG.warn('HTTP timeout')
                    #assert False
                else:
                    resp = resp.json()
                    self.LOG.debug(
                        "recv msg: " + self.convert_to_dictstr(resp))

            elif mode['protocol'][1] == "post":
                try:
                    resp = requests.post(url, headers=header,
                                         data=json.dumps(data), timeout=5)
                except requests.exceptions.ConnectTimeout:
                    self.LOG.warn('HTTP timeout')
                    #assert False
                else:
                    resp = resp.json()
                    self.LOG.debug(
                        "recv msg: " + self.convert_to_dictstr(resp))
            else:
                pass
        elif mode['protoicol'] == 'tcp':
            pass

        return resp

    def data_wash_core(self, data):
        data = re.sub(r'\'TIMENOW\'', '"%s"' % datetime.datetime.now(
        ).strftime('%Y-%m-%d %H:%M:%S'), str(data))
        m = re.findall(r'(##.*?##)', str(data))
        k = [item for item in m]
        # self.LOG.debug(str(k))
        v = [eval(item.replace('#', '')) for item in k]
        # self.LOG.debug(str(v))
        d = dict(zip(k, v))
        # self.LOG.debug(str(d))
        for d, s in d.items():
            data = data.replace(d, s)
        return data

    def data_wash(self, data):
        tmp_data = str(data)
        tmp_data = self.data_wash_core(tmp_data)
        # self.LOG.error(tmp_data)
        return eval(tmp_data)

    def action(self, actions):
        self.LOG.info('start actions...')
        for action in actions:
            if action.endswith(')'):
                self.LOG.info('action:' + "self.%s" %
                              (self.data_wash_core(action)))
                eval("self.%s" % (self.data_wash_core(action)))
            else:
                eval("self.%s()" % (self.data_wash_core(action)))
