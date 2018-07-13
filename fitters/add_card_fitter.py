#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-cardmgmtapp/cardMgmt/addCard': {
        'setup': {
            'DB': {
                'table': 'mdc.base_user',
                'where': "name='自动化1' and delete_flag=1",
                'target': [(0, 'user1_Id')],
            },

            'req': {
                'field': 'ownerUuid',
                'key': 'user1_Id',
            },
        },

        'teardown': {

        },
    },
}