#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20161005
# @version: 1.0.0.1009
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
from collections import deque

import psycopg2
import requests

import config
import fitters
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


def getlasttestcase(x):
    l = os.listdir(x)
    l.sort(key=lambda fn: os.path.getmtime(x + fn) if (not os.path.isdir(x + fn)
                                                       and (os.path.splitext(fn))[-1] == '.txt') else 0)
    return x + l[-1]


def getdate():
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))


def getwhitelist():
    if not os.path.exists(whitefile):
        return 0
    w = []
    for line in open(whitefile, 'r'):
        if '.' in line:
            line.replace("\n", "")
            w.append(line)
    return w


def gettestcase():
    try:
        return pickle.load(open(getlasttestcase(workpath + "result\\"), 'rb'))
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


def check(id, url, params, code1, header1, body1, code2, header2, body2):
    global failnum
    diff = {}
    tmp = {}
    result = {}
    result['api'] = url + " " + params
    result['test differences'] = diff
    url = (re.compile(r'://(.+)').findall(bool(url[-1] == '?') and url[0:-1] or url))[0]
    if diffstr(str(code1), str(code2)):
        tmp = {}
        diffdict(url, header1, header2, [], 'header', tmp, 1, newwhitelist)
        diffdict(url, header2, header1, [], 'header', tmp, 0, newwhitelist)
        if tmp:
            diff['response headers'] = tmp
            tmp = {}
        diffdict(url, body1, body2, [], 'body', tmp, 1, newwhitelist)
        diffdict(url, body2, body1, [], 'body', tmp, 0, newwhitelist)
        if tmp:
            diff['response body'] = tmp
    else:
        diff['response code'] = (code1, code2)
    if not diff:
        result['result'] = 'PASS'
    else:
        result['result'] = 'FAIL'
        failnum += 1
    testresults[id] = result


def update_token():
    global token
    print('update_token')
    url = "http://%s:%d/%s" % ('192.168.0.236',
                               81, "/scp-usermgmtcomponent/admin/login?username=test&password=dGVzdA==")
    print(url)
    header = {
        "FrontType": 'scp-admin-ui',
    }
    resp = requests.get(url, headers=header)
    try:
        token = resp.json()['data']['token']
        print("Get token: " + token)
    except Exception as e:
        print('get token fail![%s]' % (str(e)))


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
        LOG.info('bodys: ' + json.dumps(payload))
        try:
            r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
            LOG.warn('status_code: ' + str(r.status_code))
            try:
                LOG.warn('resp: ' + convert_to_dictstr(r.json()))
            except json.decoder.JSONDecodeError:
                LOG.warn('resp: ' + r.text)
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
        LOG.info('bodys: ' + json.dumps(payload))
        try:
            r = requests.get(url, data=payload, headers=headers, timeout=10, **attrs)
            if isinstance(r.json(), list):
                src = {'Fuck': r.json()}
            else:
                src = r.json()
            try:
                LOG.warn('resp: ' + convert_to_dictstr(src))
            except json.decoder.JSONDecodeError:
                LOG.warn('resp: ' + r.text)
        except Exception as e:
            LOG.error('error: ' + str(e))

    try:
        return (r.status_code, src, r.headers)
    except json.decoder.JSONDecodeError:
        return (r.status_code, r.text, r.headers)
    except:
        return (400, {}, {})


def jsontodict(str):
    LOG.yinfo(str)
    try:
        return json.loads(str)
    except json.decoder.JSONDecodeError:
        LOG.info('{"fuck": "' + str + '"}')
        return json.loads('{"fuck": "' + str + '"}')
    except:
        return json.loads(re.compile(r'({.+})').findall(str)[0])


def strtodict(s, sp='&', op='='):
    dict = {}

    try:
        payload = json.loads(str(s))
        return payload
    except json.decoder.JSONDecodeError:
        pass

    try:
        payload = eval(params)
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
    global testnum
    testnum += 1
    (request, response) = str.split('Response ', 1)
    (_, rid, ishttps, rurl, _, requesquery, requestheader, requestbody) = request.split('Request ')
    (_, rop, ruid, rtime, raid) = rid.replace("\n", "").split(" ")
    #LOG.debug('get %s' % rtime)
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
    responsebody = re.compile(r'body: (.+)').findall(responsebody.split("\n")[0])[0]
    if payload == '' and requestbody != '':
        payload = strtodict(requestbody.split()[-1])
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
    #LOG.debug('get %s' % rtime)
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
            break

    for item in sorted(DB_list):
        if fitters.fitters[config_url]['setup'][item]:
            update_config_from_DB(fitters.fitters[config_url]['setup'][item]['table'], fitters.fitters[config_url]
                                  ['setup'][item]['where'], fitters.fitters[config_url]['setup'][item]['target'])

    for item in req_list:
        url, body = update_req_by_config(url, body, fitters.fitters[config_url]['setup'][item])

    LOG.debug('URL after  setup: %s' % (url))
    return url, body


def teardown(url, body):
    #LOG.debug('URL before teardown: %s' % (url))
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
        if fitters.fitters[t_url]['teardown'][item]:
            update_config_from_DB(fitters.fitters[t_url]['teardown'][item]['table'], fitters.fitters[t_url]
                                  ['teardown'][item]['where'], fitters.fitters[t_url]['teardown'][item]['target'])

    for item in resp_list:
        update_config_from_resp(body, fitters.fitters[t_url]['teardown'][item])
    LOG.debug('config after teardown:')
    # config_dumps()
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
    value = config.__dict__[target['key']]
    target_field = body
    field_list = target['field'].split('.')
    if target_field:
        while field_list:
            item = field_list[0]
            LOG.warn(item)
            field_list = field_list[1:]
            if re.match(r'\*', item):
                for id in range(len(target_field)):
                    LOG.yinfo(str(id))
                    LOG.yinfo(str(target_field[id]))
                    if type(target_field[id]) == type([]) or type(target_field[id]) == type({}):
                        LOG.info('Dict')
                        subtarget_field = target_field[id]
                        subfield_list = field_list[:]
                        while subfield_list:
                            item = subfield_list[0]
                            LOG.warn(item)
                            subfield_list = subfield_list[1:]
                            if type(subtarget_field[item]) == type([]) or type(subtarget_field[item]) == type({}):
                                subtarget_field = subtarget_field[item]
                            else:
                                if target['key'] == 'store':
                                    config.__dict__[item] = subtarget_field[item]
                                else:
                                    subtarget_field[item] = config.__dict__[target['key']]
                        LOG.info(str(target_field[id]))
                    else:
                        target_field[id] = config.__dict__[target['key']]
                break

            else:
                if type(target_field[item]) == type([]) or type(target_field[item]) == type({}):
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
    LOG.info(convert_to_dictstr(config_dict))


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
    url, method, payload, headers, rtime, params, https, code1, header1, body1 = testcasebuild(str)
    url, payload = setup(url, payload)
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
    if not lasttestcase or rtime not in lasttestcase:
        body1 = jsontodict(body1)
        print("send done,checking self record...\n")
        check(rtime, url, params, code1, header1, body1, code2, header2, body2)
    else:
        print("send done,checking last test...\n")
        check(rtime, url, params, lasttestcase[rtime]['response code'], lasttestcase[rtime]
              ['response header'], lasttestcase[rtime]['response body'], code2, header2, body2)
    testcase = {}
    testcase["url"] = url
    if params == '':
        params = payload
    testcase["params"] = params
    testcase["response code"] = code2
    testcase["response header"] = dict(header2)
    testcase["response body"] = body2
    testcases[rtime] = testcase
    return (code2, body2, header2)


def fifoprocess(queue, n):
    LOG.info('Total %d case' % n)
    while True:
        try:
            n -= 1
            j = n
            str = queue.popleft()
            (code, body, header) = process(str)
            while(j > 0):
                queue.append(middleware.rule(str, body, header, queue.popleft()))
                j -= 1
            fifoprocess(queue, n)
        except IndexError:
            break


def run(dataflow):
    session = ''
    sessionid = ''
    pattern = re.compile(r'(\w+)')
    try:
        for i in open(recordfile, encoding='utf-16-le'):
            if not i.startswith("\n"):
                i = i.replace("\ufeff", "")
                session += i
            if i.startswith("Request id: "):
                id, sessionid = (int(pattern.findall(i)[4]), pattern.findall(i)[3])
                LOG.warn('find ID: %d' % id)
            if i.startswith(sessionid + " end"):
                dataflow[id] = session
                session = ''
    except Exception as e:
        print("api record file open error, exit!")
        exit()
    if os.path.exists(removefile):
        try:
            for i in open(removefile, encoding='utf-16-le'):
                if not i.startswith("\n"):
                    i = i.replace("\ufeff", "")
                    if i.startswith("Request id: "):
                        id = int(pattern.findall(i)[4])

                        if id in dataflow:
                            del dataflow[id]
        except Exception as e:
            print("api removefile file open error, exit test!")
            exit()
    dataflow = sorted(dataflow.items(), key=lambda x: x[0], reverse=False)
    n = 0
    for k, v in dataflow:
        Queue.append(v)
        n += 1
    fifoprocess(Queue, n)


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


def report():
    global testnum, failnum, newwhitelist
    testresults[' In all'] = testnum
    testresults[' pass'] = testnum - failnum
    testresults[' fail'] = failnum
    curtime = getdate()
    print("test result:")
    n = 0
    for k, v in testresults.items():
        if k not in (' In all', ' pass', ' fail'):
            print(n)
            # print(v)
            print(json.dumps(v))  # ,indent=2)
            n += 1
    not whitelist and writelog(whitefile, newwhitelist, 'str')
    not os.path.exists(workpath + "result\\") and os.makedirs(workpath + "result\\")
    writelog(workpath + "result\\%sjson.log" % curtime, testcases)
    writelog(workpath + "result\\%sresult.log" % curtime, testresults)
    writelog(workpath + "result\\%sdiff.log" % curtime, newwhitelist, 'str')
    writelog(workpath + "result\\%s.txt" % curtime, testcases, 'pickle')
    print("\n%s tests , %s pass , %s fail " % (testnum, testnum - failnum, failnum))


if __name__ == "__main__":
    global LOG
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG)
    workpath = "d:\\pythontest\\"
    if not os.path.exists(workpath):
        workpath = sys.path[0] + '\\'
    recordfile = workpath + "api\\record.gor"
    if not os.path.exists(recordfile):
        print("api record file not exist, exit test!")
        exit()
    removefile = workpath + "api\\remove.gor"
    whitefile = workpath + "config\\white.txt"
    testcase_dir = workpath + "result\\"
    whitelist = getwhitelist()
    lasttestcase = gettestcase()
    testresults = {}
    testcases = {}
    newwhitelist = {}
    Queue = deque()
    testnum = 0
    failnum = 0
    update_token()
    run({})
    report()
