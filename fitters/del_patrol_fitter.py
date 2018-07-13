#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-patrolapp/scheduleMng/insertSchedule': {
        'setup': {
            'DB': {
                'table': 'pc.patrol_param',
                'where': "param_name='##config.patrol_para_name##' and delete_flag=1",
                'target': [(0, 'patrol_para_uuid')],
            },

            'req': {
                'field': 'paramId',
                'key': 'patrol_para_uuid',
            },

            'req2': {
                'field': 'startTime',
                'value': "##get_timestr_by_diff(strf='%Y-%m-%d', seconds=1)##",
            },

            'req3': {
                'field': 'endTime',
                'value': "##get_timestr_by_diff(strf='%Y-%m-%d', days=1)##",
            },

            'req4': {
                'field': 'repeat',
                'value': "##get_timestr_by_diff(strf='%d', days=1)##",
            },
        },

        'teardown': {
            'DB': {
                'table': 'pc.patrol_plan',
                'where': "plan_name='##config.patrol_plan_name##' and delete_flag=1",
                'target': [(0, 'patrol_plan_uuid')],
            }
        },
    },

    '/scp-patrolapp/scheduleMng/deleteSchedule': {
        'setup': {
            'req': {
                'field': 'while_list',
                'key': 'patrol_plan_uuid',
            },
        },

        'teardown': {
        },
    },
}
