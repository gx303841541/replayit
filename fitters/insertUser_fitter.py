#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-mdmapp/user/insertUser': {
        'setup': {
            'req': {
                'field': 'name',
                'value': "##'小狗狗' + str(random.randint(1, 10000))##",
            },
            'req2': {
                'field': 'idenNum',
                'value': "##'21122319880707' + str(random.randint(1000, 9999))##",
            },

            'req3': {
                'field': 'phone',
                'value': "##'1881234' + str(random.randint(1000, 9999))##",
            },
        },

        'teardown': {
        },
    },

}
