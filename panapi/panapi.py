#####################
# References:
# https://github.com/ly0/baidupcsapi.git
# https://pan.baidu.com/union/document/entrance
# https://developer.baidu.com/newwiki/dev-wiki/?t=1557733846879
#
######################
import requests
import webbrowser
import os
import pickle
import time
import json
from hashlib import md5

##FIXME how to process here??
API_KEY = '0Y1W5r6dIXbQe2E0BL0CtnxI'
SECRET_KEY = '9ehDeavxGdE7AZGAEiiIUTzVvAofO9Mm'

DEBUG_ON = True
#DEBUG_ON = False

##FIXME save the token file to a specific place
TOKEN_FILE_NAME = '.token.cookie'


class PanBase(object):
    '''
    Finish login
    and provide basic request method
    '''
    def __init__(self):
        self.token_file = os.environ['HOME'] + '/'+ TOKEN_FILE_NAME
        if not self._load_token():
            self._login()

    def _load_token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                tmp_data = pickle.load(token)
                if DEBUG_ON:
                    print('Reading token')
                    print(tmp_data)
                self.access_token  = tmp_data['access_token']
                self.refresh_token = tmp_data['refresh_token']
                self.expires_in    = tmp_data['expires_in']
                timestamp          = tmp_data['timestamp']

                
                '''
                # check if we need to refresh access_token
                # refresh access_token when it will expire in
                # 10% expires_in
                '''
                if (time.time() - timestamp) > self.expires_in / 100 * 90:
                    refresh_url = f'https://openapi.baidu.com/oauth/2.0/token?grant_type=refresh_token&refresh_token={self.refresh_token}&client_id={API_KEY}&client_secret={SECRET_KEY}'
                    if DEBUG_ON:
                        print("refresh url: %s"%refresh_url)
                    result = requests.get(refresh_url)
                    if result.status_code == 200:
                        if DEBUG_ON:
                            print(result.json())
                        self.access_token = result.json()['access_token']
                        self.refresh_token = result.json()['refresh_token']
                        self.expires_in = result.json()['expires_in']

                        # save them into TOKEN_FILE
                        print("refreshing token")
                        self._save_token()
                    else:
                        print("Failed to refresh access_token!!! \
                            Maybe need to get authentication again")
                        return False
            return True
        else:
            return False

    def _save_token(self):
        tmp_data={}
        tmp_data['access_token']  = self.access_token
        tmp_data['refresh_token'] = self.refresh_token
        tmp_data['expires_in']    = self.expires_in
        tmp_data['timestamp']     = time.time()
        with open(self.token_file, 'wb') as token:
            pickle.dump(tmp_data, token, pickle.HIGHEST_PROTOCOL)
        print('ALERT!!! If you want to change user account, do remove %s first!' % self.token_file)

    #响应参数为JSON格式、UTF-8编码。
    def _login(self):
        code_url = f'https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id={API_KEY}&redirect_uri=oob&scope=basic,netdisk'
        webbrowser.open_new(code_url)

        try:
            #authentication code
            auth_code = input('输入授权码:')
        except ValueError:
            print("请输入正确的授权码")

        #获取access_token 和refresh_token
        access_token_url = f'https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code&code={auth_code}&client_id={API_KEY}&client_secret={SECRET_KEY}&redirect_uri=oob'
        result = requests.get(access_token_url)
        if DEBUG_ON:
            print("Getting access token: %d" % result.status_code)
        if result.status_code == 200:
            if DEBUG_ON:
                print(result.json())
            self.access_token = result.json()['access_token']
            self.refresh_token = result.json()['refresh_token']
            self.expires_in = result.json()['expires_in']

            # save them into TOKEN_FILE
            print('saving token info')
            self._save_token()
        else:
            self.access_token = ''
            print("Failed to get access_token!!!")

    def _request(self):
        pass

class PanAPI(PanBase):
    '''
    Interfaces for Baidu Netdisk operation
    '''
    def __init__(self):
        self.pan_base_url = 'https://pan.baidu.com/rest/2.0/xpan/'
        self.pcs_base_url = 'https://d.pcs.baidu.com/rest/2.0/pcs/'
        super(PanAPI, self).__init__()

    def user_info(self):
        '''
        ' 用户信息
        '''
        uri = self.pan_base_url + 'nas?method=uinfo'
        res = requests.get(uri, params={'access_token': self.access_token}).json()
        if res['errno'] == 0:
            if DEBUG_ON:
                print(res)
            print('-' * 10, res['baidu_name'], '-' * 10)
            if res['netdisk_name'] != '':
                print('欢迎【', res['netdisk_name'], '】')
            vip = '普通用户'
            if res['vip_type'] == 0:
                vip = '普通用户'
            elif res['vip_type'] == 1:
                vip = '普通会员'
            elif res['vip_type'] == 2:
                vip = '超级会员'
            print('等级：', vip)
            return res['vip_type']
        else:
            print('Failed to get user info!')

    def quota(self):
        '''
        '查看网盘信息
        '返回的free信息不正确
        '''
        uri = 'https://pan.baidu.com/api/quota'
        res = requests.get(uri, params={'access_token': self.access_token,'checkfree': True, 'checkexpire': True}).json()
        if res['errno'] == 0:
            if DEBUG_ON:
                print(res)
            print('-' * 10, '网盘信息' ,'-' * 10)
            if res['expire'] == True:
                print("7天内有容量到期")
            print("总容量：%d GiB" % (res['total']/1024/1024/1024))
            print("已用： %d GiB" %(res['used']/1024/1024/1024))
            print("剩余： %d GiB" %(res['free']/1024/1024/1024))
        else:
            print('Failed to get disk quota')


    def list_files(self,path='/'):
        '''
        '显示文件
        '默认是根目录
        '返回的size大小都是0？？
        '''
        uri = self.pan_base_url + 'file?method=list'

        #order: time 表示先按文件类型排序，后按修改时间排序
        res = requests.get(uri, params={'access_token': self.access_token, 'dir': path, 'order': 'time'}).json()
        if res['errno'] == 0:
            if DEBUG_ON:
                print(res)
            print('-' * 10, '文件目录 【', path, '】', '文件：', len(res['list']), '-' * 10)
            for item in res['list']:
                output = item['server_filename']
                if item['isdir']: 
                    output += ' '*5
                    output += '目录'
                else:
                    output += ' '*5
                    output += '文件'

                output += ' '*5
                output += str(item['size']//1024) + 'KiB'
                print(output)
        else:
            print("Failed to list contents")

    def search(self, path='/', filename=''):
        '''
        '搜索某个文件，默认是在根目录下
        '不区分大小写
        '按正则表达式搜索
        '''
        if filename=='':
            print("请输入要搜索的文件名")
            return -1

        uri = self.pan_base_url + 'file?method=search'
        #do the search recursively
        res = requests.get(uri, params={'access_token': self.access_token,'dir': path, 'key': filename, 'recursion': 1}).json()
        if res['errno'] == 0:
            if DEBUG_ON:
                print(res)
            print('-' * 10, '文件目录 【', path, '】', '搜索到的文件：', '-' * 10)
            if res['list']:
                for item in res['list']:
                    output = item['path']
                    print(output)
            else:
                print("没有找到文件:%s" % filename)
        else:
            print("Failed to do the search")

    def move(self, orig, dest):
        '''
        ' rename POST
        '''
        if not orig or not dest :
            print("请输入完整的源文件路径，新文件路径")
            return -1
        dest_path = os.path.dirname(dest)
        dest_name = os.path.basename(dest)
        if not dest_path or not dest_name:
            print("请输入合法的新文件路径")
            return -1
        filelist=[{'path': orig,'dest': dest_path, 'newname': dest_name,'ondup': 'fail'}]

        uri = self.pan_base_url + 'file?method=filemanager'
        uri += '&access_token='+str(self.access_token)
        uri += '&opera=move'
        data = {
                "async": 0,
                "filelist": json.dumps(filelist)
                }
        if DEBUG_ON:
            print(uri)
            print(json.dumps(filelist))
        res = requests.post(uri, data=data).json()
        if DEBUG_ON:
            print(res)
        if res['errno'] == 0:
            print("移动成功")
        else:
            print("移动失败: %d"%res['errno'])



    def copy(self, orig, dest):
        '''
        ' 复制单个文件 POST
        ' path: 源文件完整路径
        ' dest: 目的路径
        ' newname:新文件名称
        '''
        if not orig or not dest :
            print("请输入完整的源文件路径，新文件路径")
            return -1
        dest_path = os.path.dirname(dest)
        dest_name = os.path.basename(dest)
        if not dest_path or not dest_name:
            print("请输入合法的新文件路径")
            return -1
        filelist=[{'path': orig,'dest': dest_path, 'newname': dest_name,'ondup': 'fail'}]
        #filelist=[{'path': orig,'dest': dest_path, 'newname': dest_name}]

        uri = self.pan_base_url + 'file?method=filemanager'
        uri += '&access_token='+str(self.access_token)
        uri += '&opera=copy'
        data = {
                "async": 0,
                "filelist": json.dumps(filelist)
                }
        if DEBUG_ON:
            print(uri)
            print(json.dumps(filelist))
        res = requests.post(uri, data=data).json()
        if DEBUG_ON:
            print(res)
        if res['errno'] == 0:
            print("复制成功")
        else:
            print("复制失败: %d"%res['errno'])



    def remove(self, path):
        '''
        '删除文件 POST
        '一个或多个文件(以空格分开)
        '删除一个不存在的文件, errno 仍然返回0
        '''
        data = {
                "async": 1,
                "filelist": json.dumps(path.split())
                }

        uri = self.pan_base_url + 'file?method=filemanager'
        uri += '&access_token='+str(self.access_token)
        uri += '&opera=delete'

        if DEBUG_ON:
            print(uri)
            print(data)

        res = requests.post(uri, data = data).json()

        if DEBUG_ON:
            print(res)

        if res['errno'] == 0:
            print("删除成功")
        else:
            print("删除失败: %d"%res['errno'])

    def mkdir(self, path):
        '''
        '创建文件夹
        '上传文件的其中最后一个步骤
        '''
        uri = self.pan_base_url + 'file?method=create'
        uri += '&access_token='+str(self.access_token)

        data = {
                "path": path,
                "size": 0,
                "isdir": 1
                }

        if DEBUG_ON:
            print(uri)
            print(data)

        res = requests.post(uri, data = data).json()

        if DEBUG_ON:
            print(res)

        if res['errno'] == 0:
            print("创建成功")
        else:
            print("创建失败: %d"%res['errno'])




    def upload(self, orig, dest=''):
        '''
        orig: 本地文件路径
        dest: 网盘文件路径
        1\ 权限申请
        1.1 每个第三方在网盘只能拥有一个文件夹用于存储上传文件，该文件夹必须位于/apps目录下，名称可自定义。
        1.2 使用上传接口之前，请提供APPID和文件夹名称，网盘这边会进行配置。
        2上传限制
        2.1大小限制
        普通用户单个上传文件大小上限为4G
        会员用户单个上传文件大小上限为10G
        超级会员用户单个上传文件大小上限为20G
        2.2类型限制
        普通用户在网盘APP端无法上传视频、Live Photo

        #####
        总之一句话，垃圾
        =================================
        步骤：
        文件上传分为三个阶段：预上传、分片上传、创建文件。只有完成这三步，才能将文件上传到网盘。
        '''
        if not os.path.exists(orig):
            print("文件:%s 不存在" % orig)
            return -1
        #如果dest为空，则默认同文件名保存到根目录下
        if dest == '':
            dest = os.path.basename(orig)
            dest = '/' + dest

        if os.path.isfile(orig):
            size = os.path.getsize(orig)
        else:
            print("%s不是普通文件，退出" % orig)
            return -1

        '''
        备注：

        1、普通用户单个分片大小固定为4MB

        2、普通会员用户单个分片大小上限为16MB

        3、超级会员用户单个分片大小上限为32MB
        '''
        vip_type = self.user_info()

        if vip_type == 0:
            block_size = 4*1024*1024
        elif vip_type == 1:
            block_size = 16*1024*1024
        elif vip_type == 2:
            block_size = 32*1024*1024
        '''
        预上传的操作
        '''
        with open(orig, 'rb') as fid:
            first_256bytes = fid.read(256*1024)
            slice_md5 = md5(first_256bytes).hexdigest()
            content_md5 = md5(first_256bytes)
            block_list = []

            #set file offset to 0
            fid.seek(0)
            while True:
                block = fid.read(block_size)
                if not block:
                    break
                block_md5 = md5(block).hexdigest()
                content_md5.update(block)
                #append block_md5 to block_list
                block_list.append(block_md5)

        '''
        rtype:
        文件命名策略，默认0
        0 为不重命名，返回冲突
        1 为只要path冲突即重命名
        2 为path冲突且block_list不同才重命名
        3 为覆盖
        '''
        data = {
                "path": dest,
                "size": size,
                "isdir": 0,
                "autoinit": 1,
                "rtype": 3,
                "block_list": json.dumps(block_list),
                "content-md5": content_md5.hexdigest(),
                "slice_md5": slice_md5
                }

        if DEBUG_ON:
            print("预上传：")
            print("源文件：%s size: %d" % (orig, size))
            print("目的文件：%s" % dest )
            print("分片大小: %d" % block_size)
            print("slice_md5: %s" % slice_md5)
            print("content_md5: %s" %content_md5.hexdigest())
            print("block_list:")
            print(block_md5)
            print("data in POST:")
            print(data)

        # uri for PRECREATE
        uri = self.pan_base_url + "file?method=precreate"
        uri += '&access_token='+str(self.access_token)
        res = requests.post(uri, data=data).json()
        if DEBUG_ON:
            print("PRECREATE response:")
            print(res)
        if res['errno'] == 0:
            print("预创建成功")
        else:
            print("预创建失败: %d"%res['errno'])

        '''
        分片上传的操作
        '''
        ##################################
        ##################################
        ##################################
        ##################################
        '''
        分片上传的步骤，不能按照官方文档写。

        user not exists问题需要改参数

        1、此处不能带access_token参数

        2、需要加上 app_id=250528  (从web版抓出来的)

        3、要带上BDUSS参数 (这个参数网页登录百度账号，看cookie)


        获取BDUSS

        BaiduPCS-go
        '''
        ##################################
        ##################################
        ##################################
        ##################################
        upload_id = res['uploadid']
        return_type = res['return_type']
        if return_type == 1:
            print("文件在云端不存在")
        elif return_type == 2:
            print("文件在云端已存在")
            #当作上传完成
            return 0
        else:
            print("unknown return_type: %d" % return_type)

        block_list_seq = res['block_list']
        request_id = res['request_id']
        # uri for superfile2
        # different base url
        uri = self.pcs_base_url + "superfile2?method=upload"
        uri += '&access_token='+self.access_token
        #uri += '&app_id=250528&BDUSS=mwzSnhXMTZrWndJQnVlR1d5Qk5nYldYMUUzam80bjV0TTR5SmJjRVA5MzZsNmxlRVFBQUFBJCQAAAAAAAAAAAEAAACS0ThVxq~RvcauzOzRxAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPoKgl76CoJeS'
        uri += '&type=tmpfile'
        uri += '&path='+dest
        uri += '&uploadid='+upload_id
        # 上传数据
        with open(orig, 'rb') as fid:
            fid.seek(0)
            cnt = 0;
            while True:
                block = fid.read(block_size)
                if not block:
                    break
                # 判断
                if not cnt in block_list_seq:
                    print("预创建返回的block_list和申请的不一致，退出")
                    return -1
                else:
                    upload_uri = uri+"&partseq="+str(cnt)

                files = {
                        'file': (orig, fid, 'text/plain')
                        #'file': (orig, block),
                        #'file': orig, 
                        }
                cnt += 1

                if DEBUG_ON:
                    print("uri for upload: "+upload_uri)
                    #print(files)

                try:
                    #res = requests.post(upload_uri, files=json.dumps(files)).json()
                    res = requests.post(upload_uri, files=files).json()
                except OSError as err:
                    print("OS error: {0}".format(err))
                    #return -1
                '''
                except:
                    print("exception caught!")
                    return -1
                '''

                if DEBUG_ON:
                    print(res)
                if res['error_code'] == 0:
                    print("%d上传成功" % cnt)
                else:
                    print("%d上传失败: %d"%(cnt,res['errno']))





        '''
        创建文件的操作
        '''
    

    def download(self, orig, dest):
        '''
        orig: 网盘文件路径
        dest: 本地文件路径
        '''
        pass
