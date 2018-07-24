1. 安装与使用

A)自动抓包记录

安装FiddlerSetup.exe

将fiddler\fiddler.js替换到fiddler4, Rules->Customize rules，运行待测程序自动抓取数据包

利用fiddler js插件开发完成自动抓包，支持手工增加和删除，支持https

修改fiddlerjsconf.ini 指定域名，抓取的包会记录到 record.gor提供给回放所用

修改fiddler.js中 OnBeforeResponse，DoAddSession 包过滤规则

oSession.GetResponseBodyAsString().IndexOf("\"errno\":0")

手动增删：在fiddler某条记录右键选1add 或2delete

B)回放测试：
C:\replayit>python3 replayit.py -h
usage: replayit.py [-h] [-f FILE_LISTS] [-c COUNT]

--------------------------------------------------

optional arguments:
  -h, --help            show this help message and exit
  -f FILE_LISTS, --file FILE_LISTS
                        Specify replay files
  -c COUNT, --count COUNT
                        Specify how many times to replay

2. 工作原理
详见《录制回放工具介绍.pptx》


3. fitter机制说明
针对每个URL，都会先查询对应的fitter规则，根据规则对URL及消息体做修正，然后才会发出请求。响应也会根据fitter做出相应的处理。
fitter配置规则：

3.1 'setup'
支持两种配置：数据库查询与请求消息字段替换

'DB': {
    'table': 'mdc.base_user',#数据库表名
    'where': "name='自动化2' and delete_flag=1",#数据库查询过滤条件
    'target': [(0, 'user2_Id')],#数据库第1列的值赋值给config.user2_Id
},

'req': {
    'field': 'user.userId',#请求消息体中的user字段的userId字段的值会被config.user2_Id替换掉
    'key': 'user2_Id',
},

3.2 'teardown'
支持两种配置：数据库查询与响应消息字段存储备用

'resp': {
    'field': 'user.userId',#将响应消息体中的user字段的userId字段的值存储到config.user2_Id
    'key': 'user2_Id',
},
