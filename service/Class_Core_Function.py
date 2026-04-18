# coding: utf-8
"""
@Time :    12/1/2024 11:41 
@Author:  fff
@File: Class_Core_Function.py
@Software: PyCharm
; 核心函数，标准化常用项目函数调用
"""
import datetime, json, random, logging, time, psutil, os, requests, string, hashlib,concurrent.futures,ast
from urllib.parse import urlparse,unquote,urlunparse
class Class_Core_Function:
    def __init__(self):
        self.Path = os.path.dirname(__file__)
        self.Path = self.Path.replace('\\', '/')
        self.logger = logging.getLogger()
    
    def callback_config(self):
        '''
        返回配置文件
        :return: 配置字典，读取失败返回None
        '''
        try:
            with open(self.Path + '/../config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            self.logger.error(f'读取配置文件失败: {str(e)}')
            return None
    
    def callback_project_config(self):
        '''
        返回正在运行的项目配置（status_code=1）
        :return: 项目配置字典，没有运行的项目返回None
        '''
        try:
            from database.project_database import ProjectDatabase
            project_db = ProjectDatabase()
            running_project = project_db.get_running_project()
            return running_project
        except Exception as e:
            self.logger.error(f'获取项目配置失败: {str(e)}')
            return None

    def callback_logging(self):
        '''
        # 由于日志基本配置中级别设置为DEBUG，所以一下打印信息将会全部显示在控制台上
        [#]INFO: this is a loggging info message 2021-02-13 12:03:59,481 - test.py[line:6]
        logging.info('this is a loggging info message')
        logging.debug('this is a loggging debug message')
        logging.warning('this is loggging a warning message')
        logging.error('this is an loggging error message')
        logging.critical('this is a loggging critical message')
        :return:
        '''
        # logger = logging.getLogger()
        self.logger.setLevel('INFO')
        formatter = logging.Formatter("[#]%(levelname)s: %(message)s     %(asctime)s - %(filename)s[line:%(lineno)d]")
        chlr = logging.StreamHandler()  # 输出到控制台的handler
        chlr.setFormatter(formatter)
        # chlr.setLevel('INFO')  # 也可以不设置，不设置就默认用logger的level
        # 获取项目根目录（facai目录）
        project_root = os.path.dirname(self.Path)
        log_file_path = os.path.join(project_root, 'project_data', 'debug.log')
        fhlr = logging.FileHandler(log_file_path)  # 输出到文件的handler
        fhlr.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(chlr)
            self.logger.addHandler(fhlr)
        return self.logger
    
    def callback_time(self, num=0):
        '''
        0 时间+日期
        1 日期
        2 时间
        :param num:
        :return:
        '''
        if num == 1:
            #return time.strftime('%Y-%m-%d', time.localtime())
            return datetime.datetime.now().strftime('%Y-%m-%d')
        elif num == 2:
            #return time.strftime('%H-%M-%S', time.localtime())
            return datetime.datetime.now().strftime('%H:%M:%S')
        elif num == 0:
            return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def threadpool_Core_Function(self, Core_Function, lists, num):
        '''
        thread多线程池
        :fun 函数
        :lists 数据
        :num 线程数
        '''
        with concurrent.futures.ThreadPoolExecutor(num) as executor:
            executor.map(Core_Function, lists,timeout=10)
            #executor.shutdown(wait=True)
    
    def callback_split_url(self, url, type):
        '''
            callback domain
            :type
                http?s://www.xxx.com:80/aaaaa?dassda=aaa
                0 http?s://www.xxx.com:80/
                1 www.xxx.com:80
                2 www.xxx.com
                3 http?s://www.xxx.com:80/aaaaa
                4 http?s://www.xxx.com:80/aaaaa?dassda=aaa
        '''
        try:
            url = urlparse(url)
            if type == 0:
                return url.scheme + '://' + url.netloc + '/'
            elif type == 1:
                return url.netloc
            elif type == 3:
                return url.scheme + '://' + url.netloc + url.path
            elif type == 4:
                return url
            elif type == 2:
                if ':' in url.netloc:
                    return url.netloc.split(':')[0]
                return url.netloc
        except:
            return False

    def callback_port_number(self, url):
        '''
        ;return port number 返回端口号
        :param url:
        :return:
        '''
        try:
            parsed = urlparse(url)
            if parsed.port:
                return parsed.port
            else:
                if parsed.scheme == 'http':
                    return 80
                elif parsed.scheme == 'https':
                    return 443
        except:
            return False

    def callback_ranstr(self, num=8):
        # 随机字符串
        H = 'abcdefghijklmnopqrstuvwxyz0123456789.-'
        salt = random.sample(H, num)
        return ''.join(salt)

    def md5_convert(self, string):
        """
        计算字符串md5值
        :param string: 输入字符串
        :return: 字符串md5
        """
        m = hashlib.md5()
        m.update(string.encode())
        return m.hexdigest()
    
    def callback_url(self, url):
        '''
        ;标准化设置返回url
        http://192.168.0.36:80/DVWA/vulnerabilities/sqli/?id=1&Submit=Submit
        http://192.168.0.36/DVWA/vulnerabilities/sqli/?id=1&Submit=Submit
        http://WWW.tarGEt.cOm/dasdsaAdas?ASDAa=2#wadas=dadsAa
        http://www.target.com/dasdsaAdas?ASDAa=2#wadas=dadsAa
        ;把域名转换为小写
        ;把端口转换为80修改掉
        ;把443端口转换为https
        :param url:
        :return:
        '''
        url_urlparse = urlparse(url)
        netloc = url_urlparse.netloc.split(':')
        if len(netloc) == 2:
            if netloc[1] == '80':
                url = url_urlparse._replace(netloc=netloc[0]).geturl()
                url_urlparse = urlparse(url)
            elif netloc[1] == '443':
                url = url_urlparse._replace(netloc=netloc[0]).geturl()
                url_urlparse = urlparse(url)
                url = url_urlparse._replace(scheme='https').geturl()
                url_urlparse = urlparse(url)
        url = url_urlparse._replace(scheme=url_urlparse.scheme.lower(), netloc=url_urlparse.netloc.lower()).geturl()
        parsed = urlparse(url)
        lowercased_netloc = parsed.netloc.lower()
        url = urlunparse(
            parsed._replace(netloc=lowercased_netloc)
        )
        return url
    
    def callback_file_extensions(self,url):
        '''
        ;返回url扩展名
        :param url:
        :return:
        '''
        try:
            url_parse = urlparse(url)
            url_parse = os.path.splitext(url_parse.path)
            return url_parse[1].lower()
        except:
            return None
    
    def create_request(self, url):
        '''
        ;创建请求
        :param url: 目标URL
        :return: 请求字典
        '''
        # 从当前运行项目配置中获取user_agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        
        # 获取当前运行的项目配置
        running_project = self.callback_project_config()
        if running_project and 'Project' in running_project:
            project_name = running_project['Project']
            try:
                from database.project_database import ProjectDatabase
                project_db = ProjectDatabase()
                config = project_db.get_project_by_name(project_name)
                if config and 'user_agent' in config:
                    user_agent = config['user_agent']
            except Exception as e:
                self.logger.error(f'获取项目user_agent失败: {str(e)}')

        request = {}
        request['url'] = url
        request['website'] = self.callback_split_url(url, 0)
        request['method'] = "GET"
        request['headers'] = {
            "Sec-Ch-Ua": "\"(Not(A:Brand\";v=\"8\", \"Chromium\";v=\"98\"",
            "Accept": "*/*",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "User-Agent": user_agent,
            "Connection": "close", "Sec-Fetch-Site": "none", "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate", "Sec-Fetch-Mode": "navigate", "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-User": "?1", "Accept-Language": "zh-CN,zh;q=0.9", "Sec-Ch-Ua-Mobile": "?0",
            "referer": self.callback_split_url(url, 0),
            "origin": self.callback_split_url(url, 0)
        }
        request['body'] = ""
        request['status'] = 0
        request['scaner_status']=0
        request['time'] = self.callback_time(0)
        # print(request)
        return request

    def create_image_path(self):
        '''
        创建截图保存路径
        结构: project_data/{project_name}/images/{date}/
        :return: 图片保存目录路径
        '''
        # 获取当前运行的项目配置
        running_project = self.callback_project_config()
        project_name = 'default'
        if running_project and 'Project' in running_project:
            project_name = running_project['Project']
        
        # 获取当前日期
        date_str = self.callback_time(1)  # 格式: YYYY-MM-DD
        
        # 构建路径: project_data/{project_name}/images/{date}/
        project_root = os.path.dirname(self.Path)
        image_dir = os.path.join(project_root, 'project_data', project_name, 'images', date_str)
        
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        return image_dir

