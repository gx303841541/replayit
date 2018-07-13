#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-accesscontrolapp/deviceGroup/deleteDeviceGroupById': {
        'setup': {
            'DB': {
                'table': 'acc.acc_device_group',
                'where': "group_name='autotest_group3' and delete_flag=1",
                'target': [(0, 'group3_uuid')],
            },

            'req': {
                'field': 'id',
                'key': 'group3_uuid',
            },
        },

        'teardown': {
        },
    },
}