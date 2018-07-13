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
                'where': "name='自动化2' and delete_flag=1",
                'target': [(0, 'user2_Id')],
            }
        },
    },

    '/scp-cardmgmtapp/cardMgmt/addCard': {
        'setup': {
            'req': {
                'field': 'ownerUuid',
                'key': 'user2_Id',
            },
        },

        'teardown': {
        },
    },

}