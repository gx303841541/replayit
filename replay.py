#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20161005
# @version: 1.0.0.1009
import copy
import datetime
import difflib
import json
import logging
import os
import pickle
import re
import sys
import time
import urllib.parse
from collections import defaultdict, deque
from importlib import import_module
from pathlib import *

import psycopg2
import requests

import config
import middleware
from basic.log_tool import MyLogger


def convert_to_dictstr(src):
    if isinstance(src, dict):
        return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    elif isinstance(src, str):
        return json.dumps(json.loads(src), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    elif isinstance(src, bytes):
        return json.dumps(json.loads(src.decode('utf-8')), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    elif isinstance(src, list):
        src = {'Fuck': src}
        return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    else:
        LOG.error('Unknow type(%s): %s' % (src, str(type(src))))
        return None


def readfile(fpath, encoding='utf-16-le'):
    with open(fpath, 'r', encoding) as f:
        while True:
            block = f.readline()
            if block:
                yield block
            else:
                return


def get_whitelist(record):
    w = {}
    whitefile = config.white_list_dir + record.replace('.gor', '.json')
    if not os.path.exists(whitefile):
        return w
    f = open(whitefile, 'r')
    w = json.loads(f.read())
    return w


def create_whitelist(testcases, name):
    LOG.info('Create new %s' % name)
    results = defaultdict(lambda: {})
    for rtime in testcases:
        if testcases[rtime]['diff']:
            results[testcases[rtime]['url']].update(testcases[rtime]['diff'])
    fix_dict(results)
    with open(name, 'w') as f:
        f.write(json.dumps(results, sort_keys=True, indent=4,
                           separators=(',', ': '), ensure_ascii=False))


def getlasttestcase(record):
    l = os.listdir(config.result_dir)
    l.sort(key=lambda fn: os.path.getmtime(config.result_dir + fn)
           if os.path.isdir(config.result_dir + fn) else 0)
    if l:
        last_dir = config.result_dir + l[-1]
    else:
        return 0
    l = os.listdir(last_dir)
    l.sort(key=lambda fn: os.path.getmtime(last_dir + fn) if (not os.path.isdir(last_dir + fn)
                                                              and (os.path.splitext(fn))[-1] == '.txt') else 0)
    try:
        return pickle.load(open(l[-1], 'rb'))
    except Exception as e:
        return 0


def diffstr(str1, str2):
    return (difflib.SequenceMatcher(None, str(str1), str(str2))).quick_ratio() == 1.0


def setfilter(url, type):
    filter = []
    if whitelist:
        for line in whitelist:
            u, line = line.split(' ', 1)
            k, v = line.split('.', 1)
            if (k == type and url == u) or u == '*':
                filter.append(v.replace("\n", ""))
    return filter


def dictinsertdict(dicta, dictb):
    for k, v in dicta.items():
        x = dictb.get(k)
        if not isinstance(v, dict):
            dictb.update(dicta)
            return
        if x:
            dictinsertdict(v, x)
        else:
            dictb.update(dicta)


def finddiffindict2(url, dict1, key, value, path, type, info, finddiff, rule, newwhitelist):
    if isinstance(dict1, dict):
        for k, v in dict1.items():
            path.append(k)
            find = finddiffindict2(url, v, key, value, path, type,
                                   info, finddiff, rule, newwhitelist)
            if find:
                return find
            if not isinstance(v, dict):
                if k == key:
                    if rule and not diffstr(str(v), str(value)):
                        strpath = '' + type
                        for p in path:
                            strpath = strpath + '.' + p
                        strpath = url + ' ' + strpath
                        newwhitelist[strpath] = ''
                        diff = {}
                        diff[k] = (value, v)
                        plast = path.pop()
                        for p in path[::-1]:
                            tmp = diff.copy()
                            diff = {}
                            diff[p] = tmp
                        dictinsertdict(diff, info)
                        path.append(plast)
                    finddiff = 1
                    return finddiff
            path.remove(k)
    return finddiff

    diffdict(url, body1, body2, [], 'body', {}, 1, newwhitelist)


def diffdict(url, dict1, dict2, path, type, info, rule, newwhitelist):
    filter = setfilter(url, type)
    if isinstance(dict1, dict):
        for k, v in dict1.items():
            path.append(k)
            filterpath = ''
            for p in path:
                filterpath = bool(filterpath == '') and (filterpath + p)or(filterpath + '.' + p)
            if filterpath in filter or '*' in filter:
                path.remove(k)
                continue
            diffdict(url, v, dict2, path, type, info, rule, newwhitelist)
            if not isinstance(v, dict):
                find = 0
                find = finddiffindict2(url, dict2, k, v, [], type, info, find, rule, newwhitelist)
                if not find:
                    diff = {}
                    if rule == 1:
                        diff[k] = ('non-exist', v)
                        str = '' + type
                        for p in path:
                            str = str + '.' + p
                        str = url + ' ' + str
                        newwhitelist[str] = ''
                    else:
                        diff[k] = (v, 'non-exist')
                        str = '' + type
                        for p in path:
                            str = str + '.' + p
                        str = url + ' ' + str
                        newwhitelist[str] = ''
                    plast = path.pop()
                    for p in path[::-1]:
                        tmp = diff.copy()
                        diff = {}
                        diff[p] = tmp
                    info.update(diff)
                    path.append(plast)
            path.remove(k)


# just as its name implies
def list_compare(template, target):
    diff = {}
    if not isinstance(template, list) and not isinstance(target, list):
        LOG.error("template[%s] or target[%s] is not list instance!" %
                  (str(type(template)), str(type(target))))
        return 'mismatch'

    if len(template) == len(target):
        for id in range(len(template)):
            if isinstance(template[id], list) and isinstance(target[id], list):
                diff[str(id)] = list_compare(template[id], target[id])
            elif isinstance(template[id], dict) and isinstance(target[id], dict):
                diff[str(id)] = dict_compare(template[id], target[id])
    else:
        diff = 'length ' + str(len(template)) + ' vs ' + str(len(target))

    return diff


# just as its name implies
def dict_compare(template, target):
    diff = {}
    if not isinstance(template, dict) and not isinstance(target, dict):
        if isinstance(template, list) and isinstance(target, list):
            if set(template) == set(target):
                return ''
            else:
                return 'list_mismatch'
        LOG.error("template[%s] or target[%s] is not dict instance!" %
                  (str(type(template)), str(type(target))))
        return 'mismatch'
    elif not isinstance(template, dict):
        template = {'Fuck': template}

    if template == target:
        return diff
    else:
        for key in template:
            if key in target:
                if isinstance(template[key], dict) and isinstance(target[key], dict):
                    temp = dict_compare(template[key], target[key])
                    if temp:
                        diff[key] = temp
                elif isinstance(template[key], dict) or isinstance(target[key], dict):
                    diff[key] = 'missed'
                elif isinstance(template[key], list) and isinstance(target[key], list):
                    temp = list_compare(template[key], target[key])
                    if temp:
                        diff[key] = temp
                elif template[key] != target[key]:
                    diff[key] = str(template[key]) + ' vs ' + str(target[key])
                else:
                    pass
            else:
                diff[key] = 'missed'

        for key in target:
            if key in template:
                if isinstance(template[key], dict) and isinstance(target[key], dict):
                    temp = dict_compare(template[key], target[key])
                    if temp:
                        diff[key] = temp
                elif isinstance(template[key], dict) or isinstance(target[key], dict):
                    diff[key] = 'missed'
                elif isinstance(template[key], list) and isinstance(target[key], list):
                    temp = list_compare(template[key], target[key])
                    if temp:
                        diff[key] = temp
                elif template[key] != target[key]:
                    diff[key] = str(template[key]) + ' vs ' + str(target[key])
                else:
                    pass
            else:
                diff[key] = 'added'
    return diff


def dict_sub(dict1, dict2):
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                dict_sub(dict1[key], dict2[key])
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                LOG.error('white has list?')
            else:
                del(dict1[key])
        else:
            #LOG.error('skip key %s' % key)
            # LOG.warn(str(dict1.keys()))
            # LOG.warn(str(dict2.keys()))
            continue
    fix_dict(dict1)


def fix_dict(dict1):
    temp_dict = copy.deepcopy(dict1)
    for key in temp_dict:
        if isinstance(temp_dict[key], dict):
            if temp_dict[key]:
                fix_dict(dict1[key])

                if not dict1[key]:
                    del(dict1[key])
            else:
                del(dict1[key])


def check(url, code1, body1, code2, body2):
    diff = {}
    tmp = {}
    url = (re.compile(r'://(.+)').findall(bool(url[-1] == '?') and url[0:-1] or url))[0]
    if diffstr(str(code1), str(code2)):
        diff = dict_compare(body1, body2)
        fix_dict(diff)
    else:
        diff['response code'] = str(code1) + ' vs ' + str(code2)
    return diff


def update_token():
    global token
    LOG.debug('update_token')
    url = "http://%s:%d/%s" % (config.server_IP,
                               config.server_port, "/scp-usermgmtcomponent/admin/login?username=test&password=dGVzdA==")
    header = {
        "FrontType": 'scp-admin-ui',
    }
    resp = requests.get(url, headers=header)
    try:
        token = resp.json()['data']['token']
        LOG.debug("Get token: " + token)
    except Exception as e:
        LOG.debug('get token fail![%s]' % (str(e)))


def send(url, method, payload, headers, **attrs):
    if method == 'POST':
        headers["Authorization"] = token
        headers = {
            "FrontType": 'egc-mobile-ui',
            "Content-Type": 'application/json',
            "Authorization": token,
        }
        LOG.info('POST url: ' + url)
        # LOG.yinfo('head: ' + convert_to_dictstr(headers))
        LOG.debug('bodys: ' + json.dumps(payload))
        try:
            r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
            try:
                if isinstance(r.json(), list):
                    src = {'Fuck': r.json()}
                else:
                    src = r.json()
                LOG.yinfo('resp %s: ' % (str(r.status_code)) + convert_to_dictstr(src))
            except json.decoder.JSONDecodeError:
                LOG.yinfo('resp %s: ' % (str(r.status_code)) + r.text)
                src = {'Fuck': r.text}
        except Exception as e:
            LOG.error('error: ' + str(e))

    if method == 'GET':
        headers["Authorization"] = token
        headers = {
            "FrontType": 'egc-mobile-ui',
            "Content-Type": 'application/json',
            "Authorization": token,
        }
        LOG.info('GET url: ' + url)
        # LOG.yinfo('head: ' + convert_to_dictstr(headers))
        LOG.debug('bodys: ' + json.dumps(payload))
        try:
            r = requests.get(url, data=payload, headers=headers, timeout=10, **attrs)
            try:
                if isinstance(r.json(), list):
                    src = {'Fuck': r.json()}
                else:
                    src = r.json()
                LOG.yinfo('resp %s: ' % (str(r.status_code)) + convert_to_dictstr(src))
            except json.decoder.JSONDecodeError:
                LOG.yinfo('resp %s: ' % (str(r.status_code)) + r.text)
                src = {'Fuck': r.text}
        except Exception as e:
            LOG.error('error: ' + str(e))

    try:
        return (r.status_code, src, r.headers)
    except json.decoder.JSONDecodeError:
        return (r.status_code, r.text, r.headers)
    except:
        return (400, {}, {})


def jsontodict(str):
    try:
        return json.loads(str)
    except json.decoder.JSONDecodeError:
        return json.loads('{"Fuck": "' + str + '"}')
    except:
        return json.loads(re.compile(r'({.+})').findall(str)[0])


def strtodict(s, sp='&', op='='):
    dict = {}
    try:
        payload = json.loads(s)
        return payload
    except json.decoder.JSONDecodeError:
        pass

    try:
        payload = json.loads(str(s))
        return payload
    except json.decoder.JSONDecodeError:
        pass

    try:
        payload = eval(a)
        return payload
    except NameError:
        pass

    try:
        list = str.split(sp)
    except ValueError:
        return dict
    for i in list:
        try:
            k, v = i.split(op)
            dict[k] = v
        except ValueError:
            break
    return dict


def testcasebuild(str):
    def replacesplit(str):
        return str.replace("\n", "").split(" ")[-1]
    (request, response) = str.split('Response ', 1)
    (_, rid, ishttps, rurl, _, requesquery, requestheader, requestbody) = request.split('Request ')
    (_, rop, ruid, rtime, raid) = rid.replace("\n", "").split(" ")
    # LOG.debug('get %s' % rtime)
    (_, responsecode, reaponseheader, responsebody) = response.split('Response ')
    url = rurl.split('url: ')[-1].strip()
    params = replacesplit(requesquery)
    payload = ''
    if params != 'undefined':
        # url = url + '?'
        payload = strtodict(urllib.parse.unquote(params))
    else:
        params = ''
    ishttps = replacesplit(ishttps)
    method = re.compile(r'header: (\w+)').findall(requestheader.split("\n")[0])[0]
    requestheader = strtodict(requestheader, '\n', ': ')
    if 'header'in requestheader:
        del requestheader['header']
    responsecode = re.compile(r'code: (.+)').findall(responsecode.split("\n")[0])[0]
    reaponseheader = strtodict(reaponseheader, '\n', ': ')
    if 'header' in reaponseheader:
        del reaponseheader['header']
    responsebody = re.compile(r'body: (.*)').findall(responsebody.split("\n")[0])[0]
    if payload == '' and requestbody != '':
        payload = strtodict(requestbody[6:])
        # LOG.debug(requestbody[6:])
    else:
        # LOG.debug('xxx')
        pass
    # LOG.debug(requestbody)
    https = 0
    if ishttps == 'True':
        https = 1
        url = "https://" + url
    else:
        url = 'http://' + url
    # LOG.debug('get %s' % rtime)
    #LOG.debug('payload %s' % payload)
    return url, method, payload, requestheader, rtime, params, https, responsecode, reaponseheader, responsebody


################################################################
def DB_query(cmd):
    cxn = psycopg2.connect(
        database=config.PostgreSQL['db'], user=config.PostgreSQL['user'], password=config.PostgreSQL['password'], host=config.PostgreSQL['host'], port=config.PostgreSQL['port'])
    cur = cxn.cursor()
    LOG.info('exec SQL:' + cmd)
    cur.execute(cmd)
    result = cur.fetchall()

    cur.close()
    cxn.close()
    return result


def DB_sql_send(table, whichone):
    resp = None
    if whichone in ['lastone', 'firstone', 'randomone']:
        resp = DB_query('select * from %s;' % (table))
        if resp:
            if whichone == 'firstone':
                resp = resp[0]
            elif whichone == 'lastone':
                resp = resp[-1]
            else:
                resp = resp[random.randint(0, len(resp) - 1)]
        else:
            pass

    else:
        resp = DB_query(
            'select * from %s where %s;' % (table, whichone))
        if resp:
            resp = resp[0]
    LOG.debug("get from DB: " + str(resp))
    return resp


def setup(url, body):
    LOG.debug('URL before setup: %s' % (url))
    skip_flag = False
    req_list = []
    DB_list = []
    config_url = url
    for t_url in fitters.fitters:
        if re.search(r'%s' % t_url, url):
            for item in fitters.fitters[t_url]['setup']:
                if re.search(r'^req', item) and fitters.fitters[t_url]['setup'][item]:
                    req_list.append(item)
                elif re.search(r'^DB', item) and fitters.fitters[t_url]['setup'][item]:
                    DB_list.append(item)
            config_url = t_url
            if 'skip' in fitters.fitters[t_url]:
                skip_flag = fitters.fitters[t_url]['skip']
            break

    for item in sorted(DB_list):
        update_config_from_DB(fitters.fitters[config_url]['setup'][item]['table'], fitters.fitters[config_url]
                              ['setup'][item]['where'], fitters.fitters[config_url]['setup'][item]['target'])

    for item in req_list:
        url, body = update_req_by_config(url, body, fitters.fitters[config_url]['setup'][item])

    LOG.debug('URL after  setup: %s' % (url))
    return url, body, skip_flag


def teardown(url, body):
    LOG.debug('teardown start...')
    resp_list = []
    DB_list = []
    config_url = url
    for t_url in fitters.fitters:
        if re.search(r'%s' % t_url, url):
            for item in fitters.fitters[t_url]['teardown']:
                if re.search(r'^resp', item) and fitters.fitters[t_url]['teardown'][item]:
                    resp_list.append(item)
                elif re.search(r'^DB', item) and fitters.fitters[t_url]['teardown'][item]:
                    DB_list.append(item)

            config_url = t_url
            break

    for item in sorted(DB_list):
        update_config_from_DB(fitters.fitters[t_url]['teardown'][item]['table'], fitters.fitters[t_url]
                              ['teardown'][item]['where'], fitters.fitters[t_url]['teardown'][item]['target'])

    for item in resp_list:
        update_config_from_resp(body, fitters.fitters[t_url]['teardown'][item])

    LOG.debug('config info after teardown:')
    config_dumps()
    LOG.debug('teardown end')
    return body


def update_config_from_resp(body, target):
    field = target['field']
    key = target['key']

    target_field = body
    field_list = field.split('.')
    while field_list:
        item = field_list[0]
        field_list = field_list[1:]
        if type(target_field[item]) == type([]) or type(target_field[item]) == type({}):
            target_field = target_field[item]
        else:
            config.__dict__[key] = target_field[item]


def update_req_by_config(url, body, target):
    config.__dict__['store'] = 'xxoo'
    if not target['key'] in config.__dict__:
        LOG.warn('fix url: %s failed, [%s] not found in config!' % (url, target['key']))
        return url, body
    value = config.__dict__[target['key']]
    target_field = body
    field_list = target['field'].split('.')
    if target_field:
        while field_list:
            item = field_list[0]
            field_list = field_list[1:]
            if re.match(r'\*', item):
                for id in range(len(target_field)):
                    LOG.debug(str(id))
                    LOG.debug(str(target_field[id]))
                    if type(target_field[id]) == type([]) or type(target_field[id]) == type({}):
                        LOG.debug('Dict')
                        subtarget_field = target_field[id]
                        subfield_list = field_list[:]
                        while subfield_list:
                            item = subfield_list[0]
                            LOG.debug(item)
                            subfield_list = subfield_list[1:]
                            if type(subtarget_field[item]) == type([]) or type(subtarget_field[item]) == type({}):
                                subtarget_field = subtarget_field[item]
                            else:
                                if target['key'] == 'store':
                                    config.__dict__[item] = subtarget_field[item]
                                else:
                                    subtarget_field[item] = config.__dict__[target['key']]
                        LOG.debug(str(target_field[id]))
                    else:
                        target_field[id] = config.__dict__[target['key']]
                break

            else:
                if item == 'while_list':
                    body = [config.__dict__[target['key']]]
                elif type(target_field[item]) == type([]) or type(target_field[item]) == type({}):
                    target_field = target_field[item]
                else:
                    if target['key'] == 'store':
                        config.__dict__[item] = target_field[item]
                    else:
                        target_field[item] = config.__dict__[target['key']]

    if re.match(r'\w+', target['field']):
        url = re.sub(r'%s=\w+' % (target['field']), '%s=%s' % (target['field'], value), url)

    return url, body


def config_dumps():
    config_dict = {}
    for item in dir(config):
        if item.startswith('_') or (type(config.__dict__[item]) == type(os)):
            continue
        config_dict[item] = config.__dict__[item]
    LOG.debug(convert_to_dictstr(config_dict))


def update_config_from_DB(table, whichone, item_list):
    resp = DB_sql_send(table, data_wash_core(whichone))
    if not resp:
        return
    for id, key in item_list:
        LOG.debug('set config.%s = "%s"' % (key, resp[id]))
        setattr(config, key, resp[id])


def data_wash_core(data):
    data = re.sub(r'\'TIMENOW\'', '"%s"' % datetime.datetime.now(
    ).strftime('%Y-%m-%d %H:%M:%S'), str(data))
    m = re.findall(r'(##.*?##)', str(data))
    k = [item for item in m]
    # self.LOG.debug(str(k))
    v = [eval(item.replace('#', '')) for item in k]
    # self.LOG.debug(str(v))
    d = dict(zip(k, v))
    # self.LOG.debug(str(d))
    for d, s in d.items():
        data = data.replace(d, s)
    return data


def data_wash(data):
    tmp_data = str(data)
    tmp_data = data_wash_core(tmp_data)
    # self.LOG.error(tmp_data)
    return eval(tmp_data)


def process(str):
    testcase = {}
    url, method, payload, headers, rtime, params, https, code1, header1, body1 = testcasebuild(str)
    url, payload, skip_flag = setup(url, payload)
    if skip_flag:
        testcase["url"] = url
        testcase["params"] = params
        testcase["diff"] = {}
        testcase['rtime'] = rtime
        return testcase

    try:
        if https:
            (code2, body2, header2) = send(url, method, payload, headers, verify=False)
        else:
            (code2, body2, header2) = send(url, method, payload, headers)
        payload = teardown(url, body2)
    except Exception as e:
        LOG.error(str(e))
        (code2, body2, header2) = ('send except!', '{"errno":""}', {})
    # config_dumps()
    header2 = dict(header2)
    body1 = jsontodict(body1)

    diff = check(url, code1, body1, code2, body2)

    testcase["url"] = url
    if params == '':
        params = payload
    testcase["params"] = params
    testcase["response code"] = code2
    #testcase["response header"] = dict(header2)
    testcase["response body"] = body2
    testcase["diff"] = copy.deepcopy(diff)
    testcase['rtime'] = rtime
    return testcase


def writelog(file, test, type='json'):
    try:
        if type == 'json':
            return open(file, 'w').write(json.dumps(sorted(test.items(), key=lambda x: x[0], reverse=False), sort_keys=True, separators=(',', ':')))
        if type == 'str':
            fileobj = open(file, 'w')
            for k, v in test.items():
                fileobj.write(k + '\n')
            fileobj.close()
        if type == 'listtostr':
            fileobj = open(file, 'w')
            for k, v in test:
                fileobj.write(k + '\n')
            fileobj.close()
        if type == 'pickle':
            pickle.dump(test, open(file, 'wb'))
    except Exception as e:
        pass


def report(testcases):
    global sub_log_dir
    total = 0
    fail = 0
    fail_case = []
    pass_case = []

    for rtime in testcases:
        total += 1
        if testcases[rtime]['diff']:
            fail_case.append(rtime)
            fail += 1
        else:
            pass_case.append(rtime)

    # create ori diff
    ori_diff = defaultdict(lambda: {})
    for rtime in testcases:
        if testcases[rtime]['ori_diff']:
            ori_diff[rtime + ':' + testcases[rtime]['url']] = testcases[rtime]['ori_diff']
    with open(sub_log_dir + 'ori_diff.json', 'w') as f:
        f.write(json.dumps(ori_diff, sort_keys=True, indent=4,
                           separators=(',', ': '), ensure_ascii=False))

    # create result
    result = defaultdict(lambda: {})
    for rtime in testcases:
        if testcases[rtime]['diff']:
            result[rtime + ':' + testcases[rtime]['url']] = testcases[rtime]['diff']
    with open(sub_log_dir + 'result.json', 'w') as f:
        f.write(json.dumps(result, sort_keys=True, indent=4,
                           separators=(',', ': '), ensure_ascii=False))

    # create report
    with open(sub_log_dir + 'report.txt', 'w') as f:
        f.write('Total cases number: %d\n' % (total))
        f.write('PASS cases number: %d\n' % (total - fail))
        f.write('FAIL cases number: %d\n' % (fail))

        f.write('FAIL cases list:\n')
        for rtime in fail_case:
            f.write('\t%s\n' % (testcases[rtime]['url']))

        f.write('PASS cases list:\n')
        for rtime in pass_case:
            f.write('\t%s\n' % (testcases[rtime]['url']))


def get_info_from_record(recordfile):
    global LOG
    session = ''
    sessionid = ''
    dataflow = {}
    pattern = re.compile(r'(\w+)')
    try:
        for i in open(recordfile, encoding='utf-16-le'):
            if not i.startswith("\n"):
                i = i.replace("\ufeff", "")
                session += i
            if i.startswith("Request id: "):
                id, sessionid = (int(pattern.findall(i)[4]), pattern.findall(i)[3])
            if i.startswith(sessionid + " end"):
                if re.search(r'^Request url.*js$', session, re.M) or re.search(r'^Request url.*css$', session, re.M) or re.search(r'^Request url.*png$', session, re.M):
                    pass
                else:
                    LOG.debug('find ID: %d' % id)
                    dataflow[id] = session
                session = ''
    except Exception as e:
        LOG.error("record file: %s open error: %s, exit!" % (recordfile, str(e)))
        exit()

    dataflow = sorted(dataflow.items(), key=lambda x: x[0], reverse=False)

    for k, v in dataflow:
        yield v


def fix_whitelist():
    global whitelist
    for old_url in whitelist:
        new_url, _, _ = setup(old_url, {})
        if new_url != old_url:
            LOG.debug('old url: %s' % old_url)
            LOG.debug('new url: %s' % new_url)
            if new_url in whitelist:
                whitelist[new_url].update(whitelist[old_url])
            else:
                whitelist[new_url] = copy.deepcopy(whitelist[old_url])
            del(whitelist[old_url])


def _replayone(record):
    global sub_log_dir
    global whitelist
    whitelist = get_whitelist(record)
    update_token()
    testcases = {}
    LOG.info(config.record_dir + record)
    for rr_pair in get_info_from_record(config.record_dir + record):
        # LOG.warn(rr_pair)
        result = process(rr_pair)
        result["ori_diff"] = copy.deepcopy(result["diff"])

        fix_whitelist()

        if result["url"] in whitelist:
            dict_sub(result["diff"], whitelist[result["url"]])

        if result["diff"]:
            LOG.warn('url: %s' % result["url"] + convert_to_dictstr(result["diff"]))
            LOG.error('FAIL' + '\n' + '-' * 30 + '\n\n')
        else:
            LOG.info('PASS' + '\n' + '-' * 30 + '\n\n')
        testcases[result["rtime"]] = result

    if not whitelist:
        create_whitelist(testcases, config.white_list_dir + record.replace('.gor', '.json'))

    else:
        # LOG.warn(convert_to_dictstr(whitelist))
        pass

    return testcases


def replay(record_list, rLOG):
    global testresults
    testresults = {}
    global testcases
    testcases = {}
    global newwhitelist
    newwhitelist = {}
    global testnum
    testnum = 0
    global failnum
    failnum = 0
    global LOG
    LOG = rLOG

    global log_dir
    log_dir = config.result_dir + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + os.path.sep
    try:
        os.mkdir(log_dir)
    except Exception as er:
        LOG.error('Can not create log dir: %s\n[[%s]]' % (log_dirr, str(er)))
        sys.exit()

    temp_LOG = LOG
    for record in record_list:
        LOG = temp_LOG
        LOG.yinfo('To replay module: %s...' % record)
        global sub_log_dir
        sub_log_dir = log_dir + PurePosixPath(record).stem + os.path.sep
        global fitters
        fitters = import_module('fitters.' + PurePosixPath(record).stem + '_fitter')
        try:
            os.mkdir(sub_log_dir)
        except Exception as er:
            LOG.error('Can not create log dir: %s\n[[%s]]' % (sub_log_dir, str(er)))
            sys.exit()

        LOG = MyLogger(sub_log_dir + '%s.log' % PurePosixPath(record).stem, clevel=logging.DEBUG)
        report(_replayone(record))
