#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-informationreleaseapp/schedule/insert': {
        'setup': {
        },

        'teardown': {
            'DB': {
                'table': 'id.id_schedule',
                'where': "schedule_name='autotest' and delete_flag=1",
                'target': [(0, 'schedule_uuid')],
            }
        },
    },


    '/scp-informationreleaseapp/schedule/delete': {
        'setup': {
            'req': {
                'field': 'id',
                'key': 'schedule_uuid',
            },
        },

        'teardown': {
        },
    },
}
