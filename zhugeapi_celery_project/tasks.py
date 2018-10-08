#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

from __future__ import absolute_import, unicode_literals
from .celery import app
import psutil
import requests
import datetime,time
import psutil
import os
import signal


#  小程序访问动作日志的发送到企业微信
@app.task
def user_send_action_log(data):
    url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/user_send_action_log'
    # url = 'http://127.0.0.1:8000/zhugeleida/mycelery/user_send_action_log'
    post_data = {
        'data': data
    }
    print('----------小程序|公招号->访问动作日志的发送应用消息 requests调用 post_data数据 ------------>',post_data)
    requests.post(url, data=post_data)


# 企业用户生成小程序二维码 和 小程序客户生成和自己的企业用户对应的小程序二维码。
@app.task
def create_user_or_customer_small_program_qr_code(data):
    """
    :param data:    { 'user_id': '', 'customer_id':'' }         user_id 为用户ID    customer_id 为 客户ID
    :return:
    """
    url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/create_user_or_customer_qr_code'
    get_data = {
        'data': data
    }
    print(get_data)

    requests.get(url, params=get_data)


# 企业用户生成小程序海报
@app.task
def create_user_or_customer_small_program_poster(data):
    url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/create_user_or_customer_poster'
    get_data = {
        'data': data
    }
    print(get_data)

    requests.get(url, params=get_data)


# 发送模板消息。
@app.task
def user_send_template_msg_to_customer(data):
    url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/user_send_template_msg'
    get_data = {
        'data': data
    }
    print(get_data)
    requests.get(url, params=get_data)


# 发送公众号-模板消息。
@app.task
def user_send_gongzhonghao_template_msg(data):
    url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/user_send_gongzhonghao_template_msg'
    get_data = {
        'data': data
    }
    print(get_data)
    requests.get(url, params=get_data)





@app.task
def kill_phantomjs_process():
    pids = psutil.pids()

    for pid in pids:
        # print(pid)
        p = psutil.Process(pid)
        # print(p.name)
        if p.name() == 'phantomjs':
            print(pid)

            start_time  =  p.create_time()
            start_time = int(start_time)
            create_time_minute = time.localtime(start_time).tm_min

            # process_name = p.name()
            now_time = int(time.time())
            now_time_minute = time.localtime(now_time).tm_min
            if now_time_minute == create_time_minute:
                print('------ Lived process_name---->>', p.name(), '|', pid)
                continue
            else:
                print('------ kill process_name---->>',p.name(),'|',pid)
                try:
                    # cmd_name = 'kill -9  %s' % (pid)
                    # os.system(cmd_name)
                    process_ret = os.kill(pid, signal.SIGKILL)
                    print ('---- 已杀死%s pid为%s的进程, 返回值%s----->>' % (p.name(),pid,process_ret))

                except Exception as  e:
                    print ('----- Exception 没有如此进程!!!------>>')


# 获取查询最新一次提交的审核状态并记录到数据库
@app.task
def get_latest_audit_status_and_release_code():
    url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/get_latest_audit_status_and_release_code'
    get_data = {

    }

    requests.get(url, params=get_data)


