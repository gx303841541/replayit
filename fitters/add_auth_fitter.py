#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-accesscontrolapp/auths/add': {
        'setup': {
            'DB': {
                'table': 'mdc.base_user',
                'where': "name='自动化2' and delete_flag=1",
                'target': [(0, 'user2_Id')],
            },

            'req': {
                'field': 'user.userId',
                'key': 'user2_Id',
            },
        },

        'teardown': {

        },
    },
}