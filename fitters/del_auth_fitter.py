#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-accesscontrolapp/auths/enable': {
        'setup': {
            'DB': {
                'table': 'mdc.base_user',
                'where': "name='自动化2' and delete_flag=1",
                'target': [(0, 'user2_Id')],
            },

            'DB2': {
                'table': 'acc.acc_device_auth',
                'where': "user_id='##config.user2_Id##' and delete_flag=1",
                'target': [(0, 'authId')],
            },

            'req': {
                'field': 'authId',
                'key': 'authId',
            },
        },

        'teardown': {

        },
    },

    '/scp-accesscontrolapp/auths/cancel': {
        'setup': {
            'req': {
                'field': 'authId',
                'key': 'authId',
            },
        },

        'teardown': {

        },
    },
}