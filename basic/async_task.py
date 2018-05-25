#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""sync task handle
by Kobe Gong. 2018-1-3
"""

import logging
import os
import re
import struct
import sys
import threading
import time
import asyncio

from basic.log_tool import MyLogger

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class AsyncTask():
    def __init__(self, ):
        self.loop = asyncio.get_event_loop()

    def add_task(self, fun, ):
        pass

    def del_task(self, fun, ):
        pass

    def task_proc(self):
        pass


    async def do_some_work(x):
        pass

    def make_task(self, func, *arg):
        return asyncio.ensure_future(func(*arg))

    def run_task_once(self, task):
        self.loop.run_until_complete(task)

    def add_callback(self, task, fun, *arg):
        task.add_done_callback(fun)
 
    def merge_tasks(self, tasks_list):
        return asyncio.gather(*tasks_list)