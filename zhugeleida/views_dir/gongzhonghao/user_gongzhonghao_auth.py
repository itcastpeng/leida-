from django.shortcuts import render, redirect
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.smallprogram_verify import SmallProgramAddForm, LoginBindingForm

import time
import datetime

import requests
from publicFunc.condition_com import conditionCom
from ..conf import *
from zhugeapi_celery_project import tasks
from zhugeleida.public.common import action_record
import base64
import json

from zhugeleida.views_dir.admin.open_weixin_gongzhonghao import create_component_access_token
import redis

# 从微信公众号接口中获取openid等信息
def get_openid_info(get_token_data):
    # appid = get_token_data.get('appid')
    # rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)
    # key_name = 'access_token_%s' % (appid)
    # access_token_ret = rc.get(key_name)
    # if not access_token_ret:
    oauth_url = 'https://api.weixin.qq.com/sns/oauth2/component/access_token'
    # rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)
    ret = requests.get(oauth_url, params=get_token_data)
    ret_json = ret.json()

    print('------ 通过code换取access_token返回 ----->>', ret_json)

    openid = ret_json['openid']              # 授权用户唯一标识
    access_token = ret_json['access_token']  # 接口调用凭证

    # rc.set(key_name,access_token,7000)
    # access_token_ret = access_token
    ret_data = {
        'openid': openid,
        'access_token': access_token
    }

    return ret_data


@csrf_exempt
def user_gongzhonghao_auth(request, company_id):
    response = Response.ResponseObj()

    if request.method == "GET":
        print('---- request.GET -->', request.GET)

        company_id = company_id
        forms_obj = SmallProgramAddForm(request.GET)

        if forms_obj.is_valid():

            js_code = forms_obj.cleaned_data.get('code')
            state = forms_obj.cleaned_data.get('state')
            user_type = forms_obj.cleaned_data.get('user_type')
            gongzhonghao_app_obj = models.zgld_gongzhonghao_app.objects.get(company_id=company_id)

            authorization_appid = ''
            authorization_secret = ''
            if gongzhonghao_app_obj:
                authorization_appid = gongzhonghao_app_obj.authorization_appid
                authorization_secret = gongzhonghao_app_obj.authorization_secret
            appid = authorization_appid    # 公众号的唯一标识
            # secret = authorization_secret  # 公众号的appsecret
            component_appid = 'wx6ba07e6ddcdc69b3'


            component_access_token_ret = create_component_access_token()
            component_access_token = component_access_token_ret.data.get('component_access_token')

            get_token_data = {
                'appid': appid,
                'code': js_code,
                'grant_type': 'authorization_code',
                'component_appid': component_appid,
                'component_access_token': component_access_token

            }

            ret_data = get_openid_info(get_token_data)
            openid = ret_data['openid']
            access_token = ret_data['access_token']


            customer_objs = models.zgld_customer.objects.filter(
                openid=openid,
                user_type=user_type,
            )
            # 如果openid存在一条数据

            ret_data = {}
            if customer_objs:
                token = customer_objs[0].token
                client_id = customer_objs[0].id

                ret_data = {
                    'cid': client_id,
                    'token': token,
                    'is_verify': True
                }

            else:

                if state == 'snsapi_base':
                    redirect_uri = 'http://zhugeleida.zhugeyingxiao.com/admin/'
                    scope = 'snsapi_userinfo'  # snsapi_userinfo （弹出授权页面，可通过openid拿到昵称、性别、所在地。并且， 即使在未关注的情况下，只要用户授权，也能获取其信息 ）

                    authorize_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s&component_appid=%s#wechat_redirect' % (
                    appid, redirect_uri, scope, state, component_appid)
                    print('------authorize_url------>>', authorize_url)
                    ret_data = {

                        'authorize_url': authorize_url,
                        'is_verify': False
                    }


                elif state == 'snsapi_userinfo':
                    token = account.get_token(account.str_encrypt(openid))
                    obj = models.zgld_customer.objects.create(
                        token=token,
                        openid=openid,
                        user_type=user_type,  # (1 代表'微信公众号'),  (2 代表'微信小程序'),
                        # superior=customer_id,  #上级人。
                    )
                    client_id = obj.id


                    print('---------- 公众号-新用户创建成功 crete successful ---->')

                    get_user_info_url = 'https://api.weixin.qq.com/sns/userinfo'
                    get_user_info_data = {
                        'access_token': access_token,
                        'openid': openid,
                        'lang': 'zh_CN',
                    }

                    ret = requests.get(get_user_info_url, params=get_user_info_data)
                    ret_json = ret.json()
                    print('------- 拉取用户信息 接口返回----->>', ret_json)


                    if 'errcode' not  in  ret_json:

                        openid = ret_json['openid']  # 用户唯一标识
                        nickname = ret_json['nickname']  # 会话密钥
                        sex = ret_json['sex']  #
                        province = ret_json['province']  #
                        city = ret_json['city']  #
                        country = ret_json['country']    #
                        headimgurl = ret_json['headimgurl']  #

                        obj.nickname = nickname
                        obj.sex = sex
                        obj.province = province
                        obj.city = city
                        obj.country = country
                        obj.headimgurl = headimgurl
                        obj.save()

                    else:
                        errcode = ret_json.get('errcode')
                        errmsg = ret_json.get('errmsg')

                    ret_data = {
                        'cid': client_id,
                        'token': token,
                        'is_verify': True

                    }
            response.code = 200
            response.msg = "返回成功"
            response.data = ret_data

        else:
            response.code = 301
            response.msg = json.loads(forms_obj.errors.as_json())

    else:
        response.code = 402
        response.msg = "请求方式异常"

    return JsonResponse(response.__dict__)


@csrf_exempt

def create_gongzhonghao_auth_url(data):
    response = Response.ResponseObj()
    company_id = data.get('company_id')

    gongzhonghao_app_obj = models.zgld_gongzhonghao_app.objects.get(id=company_id)
    authorization_appid = gongzhonghao_app_obj.authorization_appid

    appid = authorization_appid

    redirect_uri = 'http://zhugeleida.zhugeyingxiao.com/admin/'
    scope = 'snsapi_base'   # snsapi_userinfo （弹出授权页面，可通过openid拿到昵称、性别、所在地。并且， 即使在未关注的情况下，只要用户授权，也能获取其信息 ）
    state = 'snsapi_base'
    component_appid = 'wx6ba07e6ddcdc69b3' # 三方平台-AppID

    authorize_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s&component_appid=%s#wechat_redirect' % (appid,redirect_uri,scope,state,component_appid)
    print('------authorize_url------>>',authorize_url)
    response.data = {'authorize_url': authorize_url }
    response.code = 200
    response.msg = "返回成功成功"


    return response



