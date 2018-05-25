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
import APIs.common_methods as common_methods
from case_config import config


class Checker(common_methods.CommMethod):
    def result_check(self, check_dict, resp):
        for item in check_dict:
            if item.startswith('resp-match'):
                self.LOG.info("check resp match...")
                self.resp_match_check(check_dict[item], resp)

            elif item.startswith('resp-unmatch'):
                self.LOG.info("check resp unmatch...")
                self.resp_unmatch_check(check_dict[item], resp)

            elif item.startswith('DB-match'):
                self.LOG.info("check DB match...")
                self.DB_match_check(check_dict[item])

            else:
                self.LOG.warn('More check point will be do in the feature!')

    def resp_match_check(self, expect_resp, resp):
        result = self.dict_items_compare(expect_resp, resp)
        assert result

    def resp_unmatch_check(self, expect_resp, resp):
        result = self.dict_items_compare(expect_resp, resp)
        assert not result

    def DB_match_check(self, expect_DB):
        result = True
        if len(expect_DB):
            pass
        else:
            return

        resp = self.DB_sql_send(expect_DB['table'], expect_DB['whichone'])

        if resp:
            for id, value in expect_DB['expect']:
                if expect_DB['method'] == '=':
                    if resp[id] == value:
                        self.LOG.info("%s == %s" % (resp[id], value))
                    else:
                        self.LOG.error("%s != %s" % (resp[id], value))
                        result = False

                elif expect_DB['method'] == '!=':
                    if resp[id] != value:
                        self.LOG.info("%s != %s" % (resp[id], value))
                    else:
                        self.LOG.error("%s == %s" % (resp[id], value))
                        result = False

                elif expect_DB['method'] == '~':
                    if re.search(r'%s' % str(value), str(resp[id])):
                        self.LOG.info("%s ~ %s" % (resp[id], value))
                    else:
                        self.LOG.error("%s !~ %s" % (resp[id], value))
                        result = False

                elif expect_DB['method'] == '!~':
                    if not re.search(r'%s' % str(value), str(resp[id])):
                        self.LOG.info("%s !~ %s" % (resp[id], value))
                    else:
                        self.LOG.error("%s ~ %s" % (resp[id], value))
                        result = False

                elif expect_DB['method'] == 'exist':
                    pass

                else:
                    self.LOG.error("Unknow method: %s!" %
                                   (expect_DB['method']))
                    result = False

        else:
            if expect_DB['method'] == 'unexist':
                pass
            else:
                self.LOG.error("%s:%s unexist!" %
                               (expect_DB['table'], expect_DB['whichone']))
                result = False
        assert result

    def DB_query(self, cmd):
        if not hasattr(self, 'cur'):
            self.cxn = psycopg2.connect(
                database=config.PostgreSQL['db'], user=config.PostgreSQL['user'], password=config.PostgreSQL['password'], host=config.PostgreSQL['host'], port=config.PostgreSQL['port'])
            self.cur = self.cxn.cursor()
        self.LOG.info('exec SQL:' + cmd)
        self.cur.execute(cmd)
        return self.cur.fetchall()

    def DB_close(self):
        self.cur.close()
        self.cxn.close()

    def DB_sql_send(self, table, whichone):
        resp = None
        if whichone in ['lastone', 'firstone', 'randomone']:
            resp = self.DB_query('select * from %s;' % (table))
            if resp:
                if whichone == 'firstone':
                    resp = resp[0]
                elif whichone == 'lastone':
                    resp = resp[-1]
                else:
                    resp = resp[random.randint(0, len(resp) - 1)]
            else:
                pass

        else:
            resp = self.DB_query(
                'select * from %s where %s;' % (table, whichone))
            if resp:
                resp = resp[0]
        self.LOG.debug("get from DB: " + str(resp))
        return resp
