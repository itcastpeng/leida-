
from zhugeleida import models
from publicFunc import Response

import json
from zhugeapi_celery_project import tasks
import base64
import qrcode
from django.conf import settings
import os,datetime
import redis
import requests
from django.http import JsonResponse, HttpResponse


def action_record(data,remark):
    response = Response.ResponseObj()
    user_id = data.get('uid')  # 用户 id
    customer_id = data.get('user_id')  # 客户 id
    article_id = data.get('article_id')  # 客户 id
    action = data.get('action')

    print('----- customer_id |  user_id | action ----->>',customer_id,user_id,action)
    company_id = models.zgld_userprofile.objects.filter(id=user_id)[0].company_id

    company_obj = models.zgld_company.objects.get(id=company_id)
    agent_id = models.zgld_app.objects.get(company_id=company_id, app_type=1).agent_id
    account_expired_time = company_obj.account_expired_time

    customer_name = models.zgld_customer.objects.get(id=customer_id).username
    customer_name = base64.b64decode(customer_name)
    customer_name = str(customer_name, 'utf-8')

    if datetime.datetime.now() <= account_expired_time:

        if action in [0]: # 只发消息，不用记录日志。


            data['content'] = '%s%s' % (customer_name, remark)
            data['agentid'] = agent_id

            tasks.user_send_action_log.delay(json.dumps(data))
            response.code = 200
            response.msg = '发送消息提示成功'

        elif action in [14,15,16]:
            # 创建访问日志
            models.zgld_accesslog.objects.create(
                user_id=user_id,
                article_id=article_id,
                customer_id=customer_id,
                remark=remark,
                action=action
            )
            print('------ 客户姓名 + 访问日志信息------->>', customer_name, remark)

            data['content'] = '%s%s' % (customer_name, remark)
            data['agentid'] = agent_id
            print('------------ [公众号] 传给tasks.celery的 json.dumps 数据 ------------------>>', json.dumps(data))

            tasks.user_send_action_log.delay(json.dumps(data))
            response.code = 200
            response.msg = '发送消息提示成功'

        else:
            # 创建访问日志
            models.zgld_accesslog.objects.create(
                user_id=user_id,
                customer_id=customer_id,
                remark=remark,
                action=action
            )

            # 查询客户与用户是否已经建立关系
            follow_objs = models.zgld_user_customer_belonger.objects.select_related('user', 'customer').filter(
                user_id=user_id,
                customer_id=customer_id
            )
            now_time = datetime.datetime.now()
            if follow_objs:  # 已经有关系了
                follow_objs.update(
                    last_activity_time=now_time
                   )

                print('------ 客户姓名 + 访问日志信息------->>', customer_name, remark)
                data['content'] = '%s%s' % (customer_name,remark)
                data['agentid'] = agent_id

                print('------------ 传给tasks.celery的 json.dumps 数据 ------------------>>',json.dumps(data))
                ret = tasks.user_send_action_log.delay(json.dumps(data))
                print('--- 记录_动作日志_log ret -->', ret)

                response.code = 200
                response.msg = '记录日志成功'

    else:
        company_name = company_obj.name
        response.code = 403
        response.msg = '账户过期'
        print('-------- 雷达账户过期: %s-%s | 过期时间:%s ------->>' % (company_id,company_name,account_expired_time))


    return response


def create_qrcode(data):
    url = data.get('url')
    article_id = data.get('article_id')

    response = Response.ResponseObj()
    qr=qrcode.QRCode(version =7,error_correction = qrcode.constants.ERROR_CORRECT_L,box_size=4,border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    img.show()

    now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    BASE_DIR = os.path.join(settings.BASE_DIR, 'statics', 'zhugeleida', 'imgs', 'gongzhonghao', 'article')

    qr_code_name = '/article_%s_%s_qrCode.jpg' % (article_id, now_time)
    path_qr_code_name = BASE_DIR + qr_code_name
    qr_url = 'statics/zhugeleida/imgs/gongzhonghao/article%s' % (qr_code_name)

    img.save(path_qr_code_name)
    response.data = {'pre_qrcode_url': qr_url}
    response.code = 200
    response.msg = '生成文章体验二维码成功'
    print('---------生成文章体验二维码成功--------->>', qr_url)

    return response

def create_scan_code_userinfo_qrcode(data):
    url = data.get('url')
    admin_uid = data.get('admin_uid')

    response = Response.ResponseObj()
    qr=qrcode.QRCode(version =7,error_correction = qrcode.constants.ERROR_CORRECT_L,box_size=4,border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    img.show()

    now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    BASE_DIR = os.path.join(settings.BASE_DIR, 'statics', 'zhugeleida', 'imgs', 'admin', 'qr_code')

    qr_code_name = '/admin_uid_%s_%s_qrCode.jpg' % (admin_uid, now_time)
    path_qr_code_name = BASE_DIR + qr_code_name
    qr_url = 'statics/zhugeleida/imgs/admin/qr_code%s' % (qr_code_name)

    img.save(path_qr_code_name)
    response.data = {'qrcode_url': qr_url}
    response.code = 200
    response.msg = '生成文章体验二维码成功'
    print('---------生成文章体验二维码成功--------->>', qr_url)


    return response


## 把秒数换换成 时|分|秒
def  conversion_seconds_hms(seconds):

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    time = 0
    if not h and not m and s:
        print("%s秒" % (s))
        time = "%s秒" % (s)
    elif not h and m and s:
        print("%s分%s秒" % (m, s))
        time = "%s分%s秒" % (m, s)

    elif h and m and s:
        print("%s时%s分%s秒" % (h, m, s))
        time = "%s时%s分%s秒" % (h, m, s)
    return time


## 生成请 第三方平台自己的 suite_access_token
def  create_suite_access_token():
    rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)
    response = Response.ResponseObj()

    SuiteId = 'wx5d26a7a856b22bec'
    key_name = 'SuiteTicket_%s' % (SuiteId)

    SuiteTicket = rc.get(key_name)
    suite_secret = 'vHBmQNLTkm2FF61pj7gqoQVNFP5fr5J0avEzYRdzr2k'

    post_component_data = {
        "suite_id": SuiteId,
        "suite_secret": suite_secret ,
        "suite_ticket": SuiteTicket
    }

    token_ret = rc.get('suite_access_token')
    print('--- Redis里存储的 suite_access_token---->>', token_ret)

    if not token_ret:
        post_component_url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token'
        component_token_ret = requests.post(post_component_url, data=json.dumps(post_component_data))
        print('--------- [企业微信]获取第三方平台 component_token_ret.json --------->>', component_token_ret.json())
        component_token_ret = component_token_ret.json()
        access_token = component_token_ret.get('suite_access_token')

        if access_token:
            token_ret = access_token
            rc.set('suite_access_token', access_token, 7000)
        else:
            response.code = 400
            response.msg = "-------- [企业微信] 获取第三方平台 component_token_ret 返回错误 ------->"
            return JsonResponse(response.__dict__)

    response.data = {
        'suite_access_token': token_ret
    }
    response.code = 200

    return response

## 企业微信 生成 预授权码
def create_pre_auth_code():
    rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)
    response = Response.ResponseObj()

    pre_auth_code_key_name = 'pre_auth_code_qiyeweixin'
    exist_pre_auth_code = rc.get(pre_auth_code_key_name)
    suite_access_token_ret = create_suite_access_token()
    suite_access_token = suite_access_token_ret.data.get('suite_access_token')


    if not exist_pre_auth_code:
        get_pre_auth_data = {
            'suite_access_token': suite_access_token
        }
        pre_auth_code_url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_pre_auth_code'
        pre_auth_code_ret = requests.get(pre_auth_code_url, params=get_pre_auth_data)
        pre_auth_code_ret = pre_auth_code_ret.json()
        pre_auth_code = pre_auth_code_ret.get('pre_auth_code')
        print('------ [企业微信] 获取第三方平台 pre_auth_code 预授权码 ----->', pre_auth_code_ret)
        if pre_auth_code:
            rc.set(pre_auth_code_key_name, pre_auth_code, 1600)
        else:
            response.code = 400
            response.msg = "--------- [企业微信] 获取第三方平台 pre_auth_code预授权码 返回错误 ------->"
            return JsonResponse(response.__dict__)
    else:
        pre_auth_code = exist_pre_auth_code

    response.data = {
        'pre_auth_code': pre_auth_code,
        'suite_access_token': suite_access_token
    }
    response.code = 200

    return response

