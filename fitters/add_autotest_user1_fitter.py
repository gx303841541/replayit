#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-mdmapp/user/insertUser': {
        'setup': {
        },

        'teardown': {
            'DB': {
                'table': 'mdc.base_user',
                'where': "name='自动化1' and delete_flag=1",
                'target': [(0, 'user1_Id')],
            }
        },
    },

    '/scp-accesscontrolapp/auths/add': {
        'setup': {
            'req': {
                'field': 'user.userId',
                'key': 'user1_Id',
            },
        },

        'teardown': {
        },
    },
}