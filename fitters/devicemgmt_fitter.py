#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import config

fitters = {
    '/scp-devicemgmtcomponent/register/insertParentDevice': {
        'setup': {
            'req': {
                'field': 'deviceName',
                'key': 'store',
            },
        },

        'teardown': {
            'resp': {
            },

            'DB': {
                'table': 'dm.dm_device',
                'where': "device_name='##config.deviceName##' and delete_flag=1",
                'target': [(0, 'device_uuid')],
            }
        },
    },

    '/scp-devicemgmtcomponent/register/updateParentDevice': {
        'setup': {
            'req': {
                'field': 'uuid',
                'key': 'device_uuid',
            },
            'req2': {
                'field': 'listDmDeviceAttrValue.*.deviceUuid',
                'key': 'device_uuid',
            },
        },

        'teardown': {
        },
    },

    '/scp-devicemgmtcomponent/register/deleteParentDevice': {
        'setup': {
            'req': {
                'field': 'id',
                'key': 'device_uuid',
            },
            'DB': {
            }
        },

        'teardown': {
        },
    },

    '/devicemgmt/deviceregister': {
        'skip': True,
        'setup': {
        },

        'teardown': {
        },
    },

    '/scp-devicemgmtcomponent/register/getDeviceList': {
        'skip': True,
        'setup': {
        },

        'teardown': {
        },
    },

    '/scp-devicemgmtcomponent/register/getDeviceSelectList/': {
        'skip': True,
        'setup': {
        },

        'teardown': {
        },
    },

    '/scp-devicemgmtcomponent/attr/getDeviceList': {
        'skip': True,
        'setup': {
        },

        'teardown': {
        },
    },

    '/scp-devicemgmtcomponent/status/getDeviceList': {
        'skip': True,
        'setup': {
        },

        'teardown': {
        },
    },
}
