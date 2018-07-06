#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import time
import requests
from requests.packages import urllib3
urllib3.disable_warnings()
from requests.exceptions import TooManyRedirects,ConnectionError,ReadTimeout,ConnectTimeout
from requests.adapters import HTTPAdapter
from urllib3.exceptions import  LocationValueError
import json
from multiprocessing import Pool
# 导入配置文件
from config import *

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()



def write_log(e):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.log')
    with open(log_file,'a+') as f:
        f.write(e)




def fault_post(domain_obj,event_type_id):
    submitData = {
        'status': event_type_id,
        'node': NODE,
        'url_id': domain_obj['id'],
        'domain': domain_obj['url'],
        'time': int(time.time()),
        'http_code': None,
        'total_time': None,
        'datetime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    fault_response = requests.post("http://" + SERVER + ":" + PORT + "/webmoni/api/check_result_submit/",
                                  data={'submitData':json.dumps(submitData)})
    result = json.loads(fault_response.text)
    if result.get('code') != 0:
        write_log(result.get('data'))
    return True

# 域名检测
def checkDomain(domain_obj):
    # 拼接url

    url = 'https://' + domain_obj['url']
    # # url = 'https://' + 'www.tt589.net'
    # 提交请求
    # start_time = time.time()
    #print(url)
    try:
        requests.adapters.DEFAULT_RETRIES = 5
        headers = {
            'Connection': 'close',
        }
        s = requests.session()
        s.keep_alive = False
        start_time = time.time()
        response = s.get(url,timeout=20,verify=False,headers=headers)
        stop_time = time.time()
        total_time = int((stop_time - start_time) * 1000)
        submitData = {
            'status':100,
            'node': NODE,
            'url_id': domain_obj['id'],
            'domain': domain_obj['url'],
            'time': int(time.time()),
            'http_code': response.status_code,
            'total_time': total_time,
            'datetime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        normal_response = s.post("http://" + SERVER + ":" + PORT + "/webmoni/api/check_result_submit/",
                                 data={'submitData':json.dumps(submitData)},headers=headers)
        result = json.loads(normal_response.text)
        if result['code'] != 0:
            write_log(result['data'])
        return True

    except ReadTimeout as e:
        fault_post(domain_obj,3)
        return False
    except LocationValueError as e:
        fault_post(domain_obj,4)
        return False
    except TooManyRedirects as e:
        fault_post(domain_obj,5)
        return False
    except ConnectTimeout as e:
        fault_post(domain_obj,3)
        return False
    except ConnectionError as e:
        fault_post(domain_obj,7)
        return False
    except Exception as e:
        fault_post(domain_obj, 99)
        write_log(e)




def main():
    # 这里开始轮询
    while True:
        # 设定轮询间隔时间
        print('Begin')
        time_remaining = INTERVAL - time.time() % INTERVAL
        # 整点开始
        time.sleep(time_remaining + 1)

        # 发送API请求 获取所有域名对象,连接失败会重试3次,
        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=3))

        domain_all_response = session.post("http://"+ SERVER +":"+ PORT +"/webmoni/api/domain_all/", data={'node': NODE})
        # 重试3次依旧失败就发送邮件并写入错误日志,退出程序

        # 获取API返回的域名对象,放入检查域名的进程池检查
        domain_all = json.loads(domain_all_response.text)
        if domain_all['code'] == 0:
            # 创建进程池，进程数=THREAD_NUM，进程调用函数main，参数url_t
            pool = Pool(THREAD_NUM)
            for domain_obj in domain_all['data']:
                if domain_obj['check_id'] == 0:
                    pool.apply_async(func=checkDomain, args=(domain_obj,))
            # 终止创建子进程
            pool.close()
            # 等待所有子进程结束
            pool.join()
            print('End')


if __name__ == '__main__':
    pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OPcenter-slave.pid')
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    main()

