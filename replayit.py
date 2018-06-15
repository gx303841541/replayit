#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
by Kobe Gong. 2018-5-15
"""


import argparse
import copy
import datetime
import decimal
import json
import logging
import os
import random
import re
import shutil
import sys
import threading
import time
from cmd import Cmd
from collections import defaultdict

import config
from basic.cprint import cprint
from basic.log_tool import MyLogger
from replay import replay


class ArgHandle():
    def __init__(self):
        self.parser = self.build_option_parser("-" * 50)

    def build_option_parser(self, description):
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            '-f', '--file',
            dest='file_lists',
            action='append',
            default=[],
            help='Specify replay files',
        )
        return parser

    def get_args(self, attrname):
        return getattr(self.args, attrname)

    def check_args(self):
        global ipv4_list

    def run(self):
        self.args = self.parser.parse_args()
        cprint.notice_p("CMD line: " + str(self.args))
        self.check_args()


class MyCmd(Cmd):
    def __init__(self, logger):
        Cmd.__init__(self)
        self.prompt = ">"
        self.LOG = logger

    def help_log(self):
        cprint.notice_p(
            "change logger level: log {0:critical, 1:error, 2:warning, 3:info, 4:debug}")

    def default(self, arg, opts=None):
        try:
            subprocess.call(arg, shell=True)
        except:
            pass

    def emptyline(self):
        pass

    def help_exit(self):
        print("Will exit")

    def do_exit(self, arg, opts=None):
        cprint.notice_p("Exit CLI, good luck!")
        sys_cleanup()
        sys.exit()


def sys_init():
    # sys log init
    global LOG
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace(
        'py', 'log'), clevel=logging.DEBUG, renable=False)
    global cprint
    cprint = cprint(os.path.abspath(sys.argv[0]).replace('py', 'log'))

    # cmd arg init
    global arg_handle
    arg_handle = ArgHandle()
    arg_handle.run()
    LOG.info("Let's go!!!")


def sys_cleanup():
    LOG.info("Goodbye!!!")
    sys.exit()


if __name__ == '__main__':
    sys_init()

    # get replay recoreds
    if arg_handle.get_args('file_lists'):
        replay(arg_handle.get_args('file_lists'), LOG)
    elif config.replay_files:
        replay(config.replay_files, LOG)
    else:
        LOG.error('No record file given!')

    my_cmd = MyCmd(logger=LOG)
    # my_cmd.cmdloop()
    sys_cleanup()
