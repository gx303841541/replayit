#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATS framework
by Kobe Gong 2017-8-21
use:
    define testcase interface follow nose's case
"""

import datetime
import logging
import os
import re
import sys
import traceback
from abc import ABCMeta, abstractmethod

import APIs.common_APIs as common_APIs
import case_config.config as config
from basic.log_tool import MyLogger

#from nose.tools import assert_equal, istest, nottest, with_setup


# define testcase which can be find by nose


class TestCase(object):
    __metaclass__ = ABCMeta

    def _init_(self, name, log_dir):
        self.name = name
        self.log_dir = log_dir
        self.log_dir += os.path.sep + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + \
            '-' + self.name + os.path.sep
        self.log_dir = common_APIs.dirit(self.log_dir)
        try:
            os.mkdir(self.log_dir)
        except Exception as er:
            print('Can not create log dir: %s\n[[%s]]' % (
                self.log_dir, str(er)))
            sys.exit()

        # create the log obj
        self.LOG = MyLogger(self.log_dir + 'output.log',
                            cenable=True, with_print=True)

    def setup(self):
        pass

    def teardown(self):
        pass

    #@istest
    #@with_setup(setup, teardown)
    def test(self):
        self.common_init()
        result = 0
        try:
            result = self.run()
        # except Exception as e:
        #    traceback.print_exc()
        #    self.LOG.critical(str(e))
        #    assert False
        finally:
            self.common_cleanup()

    @abstractmethod
    def run(self):
        pass

    def common_init(self):
        pass

    def common_cleanup(self):
        pass

    def case_pass(self, success_info='pass'):
        self.LOG.info(success_info)
        assert True
        return True

    def case_fail(self, error_info='fail'):
        self.LOG.error(error_info)
        assert False
        return False

    def do_setup(self, config_data):
        self.LOG.info('call do_setup')
        if 'setup' in config_data:
            self.LOG.info('Maybe have data')
            setup_list = config_data['setup']
            for i in setup_list:
                for k in i:
                    self.LOG.info(k)

    def do_run(self, config_data):
        self.LOG.info('call core')

    def do_teardown(self, config_data):
        self.LOG.info('call do_teardown')
