#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-devicemgmtcomponent/register/insertParentDevice': {
        'setup': {
        },

        'teardown': {
            'DB': {
                'table': 'dm.dm_device',
                'where': "device_name='autotest_screen1' and delete_flag=1",
                'target': [(0, 'device_uuid')],
            }
        },
    },

    '/scp-devicemgmtcomponent/register/insertSubDevice/': {
        'setup': {
            'req': {
                'field': 'uuid',
                'key': 'device_uuid',
            },
        },

        'teardown': {
        },
    },
}