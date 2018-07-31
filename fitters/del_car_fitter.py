#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-parkinglotapp/parkInOutMgmt/deleteCarInRecord': {
        'setup': {
            'DB': {
                'table': 'plc.park_access_cur',
                'where': "car_num='12345678' and delete_flag=1",
                'target': [(0, 'car_uuid')],
            },

            'req': {
                'field': 'ids',
                'key': 'car_uuid',
            },
        },

        'teardown': {
        },
    },
}