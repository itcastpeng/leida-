from django.shortcuts import render, redirect
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.gongzhonghao.gongzhonghao_verify import GongzhonghaoAddForm,LoginBindingForm

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

    print('-------- 通过code换取 access_token、openid信息等  返回 ------->>', ret_json)

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
def user_gongzhonghao_auth(request):
    response = Response.ResponseObj()

    if request.method == "GET":
        # <QueryDict: {'code': ['071uPB5w1EudCa0g6b5w1ZAt5w1uPB5U'], 'state': ['snsapi_base'], 'relate': ['article_id_2|pid_|level_1'], 'appid': ['wxa77213c591897a13']}>

        print('-------- 公众号-登录验证 request.GET 数据 -->', request.GET)

        js_code = request.GET.get('code')
        state = request.GET.get('state')
        appid = request.GET.get('appid')
        relate = request.GET.get('relate')
        article_id = relate.split('|')[0].split('_')[2]
        pid = relate.split('|')[1].split('_')[1]
        level = relate.split('|')[2].split('_')[1]
        uid = relate.split('|')[3].split('_')[1]

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
        redirect_url = ''
        # 判断静默和非静默方式
        # 静默方式
        if state == 'snsapi_base':
            customer_objs = models.zgld_customer.objects.filter(
                openid=openid,
                user_type=1,  # 公众号
            )

            # openid 存在数据库中
            if customer_objs:
                token = customer_objs[0].token
                client_id = customer_objs[0].id

                redirect_url = 'http://zhugeleida.zhugeyingxiao.com/#/gongzhonghao/yulanneirong/{article_id}?token={token}&user_id={client_id}&uid={uid}&level={level}&pid={pid}'.format(
                    article_id=article_id,
                    token=token,
                    client_id=client_id,

                    uid=uid,  # 文章作者-ID
                    level=level,  # 所在层级
                    pid=pid  # 目前所在的父级ID


                )

            else:
                redirect_uri = 'http://api.zhugeyingxiao.com/zhugeleida/gongzhonghao/work_gongzhonghao_auth?relate=article_id_%s|pid_%s|level_%s|uid_%s' % (article_id, pid,level,uid)
                redirect_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid={appid}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={scope}&component_appid={component_appid}#wechat_redirect'.format(
                    appid=appid,
                    redirect_uri=redirect_uri,
                    scope='snsapi_userinfo',
                    component_appid=component_appid
                )
                print('--------- 当认证登录时判断是首次登录, 返回非静默方式 snsapi_userinfo URL 登录------>>', redirect_url)

        # 非静默
        else:
            print('ret_data -->', ret_data)
            get_user_info_url = 'https://api.weixin.qq.com/sns/userinfo'
            get_user_info_data = {
                'access_token': access_token,
                'openid': openid,
                'lang': 'zh_CN',
            }

            ret = requests.get(get_user_info_url, params=get_user_info_data)
            ret.encoding = 'utf-8'
            ret_json = ret.json()
            print('----------- 【公众号】拉取用户信息 接口返回 ---------->>', ret_json)

            if 'errcode' not in ret_json:
                openid = ret_json['openid']  # 用户唯一标识
                nickname = ret_json['nickname']  # 会话密钥

                encodestr = base64.b64encode(nickname.encode('utf-8'))
                customer_name = str(encodestr, 'utf-8')

                sex = ret_json['sex']  #
                province = ret_json['province']  #
                city = ret_json['city']  #
                country = ret_json['country']    #
                headimgurl = ret_json['headimgurl']  #
                token = account.get_token(account.str_encrypt(openid))
                obj = models.zgld_customer.objects.create(
                    token=token,
                    openid=openid,
                    user_type=1,  # (1 代表'微信公众号'),  (2 代表'微信小程序'),
                    username=customer_name,
                    sex=sex,
                    province=province,
                    city=city,
                    country=country,
                    headimgurl=headimgurl,
                )
                print('---------- 公众号-新用户创建成功 crete successful ---->')

                redirect_url = 'http://zhugeleida.zhugeyingxiao.com/#/gongzhonghao/yulanneirong/{article_id}?token={token}&user_id={client_id}&uid={uid}&level={level}&pid={pid}'.format(
                    article_id=article_id,
                    token=token,
                    client_id=obj.id,

                    uid = uid,  # 文章作者-ID
                    level = level,  # 所在层级
                    pid = pid       # 目前所在的父级ID
                )
                data = {
                    'article_id' : article_id,
                    'user_id' : uid,       # 文章作者-ID
                    'customer_id' : obj.id,
                    'level' : level,
                    'pid' : pid
                }
                binding_article_customer_relate(data)

            else:
                errcode = ret_json.get('errcode')
                errmsg = ret_json.get('errmsg')
                print('---------【公众号】拉取用户信息 报错：errcode | errmsg----------->>', errcode, "|", errmsg)

        print('-----------  微信-本次回调给我code后, 让其跳转的 redirect_url是： -------->>',redirect_url)
        return redirect(redirect_url)

    else:
        response.code = 402
        response.msg = "请求方式异常"

    return JsonResponse(response.__dict__)



def create_gongzhonghao_auth_url(data):
    response = Response.ResponseObj()
    pid = data.get('pid')
    level = data.get('level')
    company_id = data.get('company_id')
    article_id = data.get('article_id')
    uid = data.get('uid')

    gongzhonghao_app_obj = models.zgld_gongzhonghao_app.objects.get(id=company_id)
    authorization_appid = gongzhonghao_app_obj.authorization_appid

    appid = authorization_appid

    # redirect_uri = 'http://zhugeleida.zhugeyingxiao.com/admin/gongzhonghao/yulanneirong/%s?relate=pid_%s|level_%s' % (article_id,pid,level)
    # redirect_uri = 'http://api.zhugeyingxiao.com/gongzhonghao/yulanneirong/%s?relate=pid_%s|level_%s' % (article_id,pid,level)
    redirect_uri = 'http://api.zhugeyingxiao.com/zhugeleida/gongzhonghao/work_gongzhonghao_auth?relate=article_id_%s|pid_%s|level_%s|uid_%s' % (article_id,pid,level,uid)

    print('redirect_uri ------->', redirect_uri)
    scope = 'snsapi_base'   # snsapi_userinfo （弹出授权页面，可通过openid拿到昵称、性别、所在地。并且， 即使在未关注的情况下，只要用户授权，也能获取其信息 ）
    state = 'snsapi_base'
    component_appid = 'wx6ba07e6ddcdc69b3' # 三方平台-AppID

    authorize_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s&component_appid=%s#wechat_redirect' % (appid,redirect_uri,scope,state,component_appid)
    print('------ 【默认】生成的静默方式登录的 snsapi_base URL：------>>',authorize_url)
    response.data = {'authorize_url': authorize_url }
    response.code = 200
    response.msg = "返回成功成功"


    return response



def binding_article_customer_relate(data):

    response = Response.ResponseObj()

    article_id = data.get('article_id')    # 公众号文章ID
    customer_id = data.get('customer_id')  # 公众号客户ID
    user_id = data.get('user_id')  # 公众号客户ID
    level = data.get('level')  # 公众号层级
    parent_id = data.get('pid')  # 所属的父级的客户ID。为空代表第一级。

    article_to_customer_belonger_obj = models.zgld_article_to_customer_belonger.objects.filter(
        article_id=article_id,
        customer_id=customer_id,
        # customer_parent_id=parent_id
    )

    if article_to_customer_belonger_obj:
        response.code = 302
        response.msg = "文章和客户关系存在"

    else:
        models.zgld_article_to_customer_belonger.objects.create(
            article_id=article_id,
            customer_id=customer_id,
            user_id=user_id,
            customer_parent_id=parent_id,
            level=level,
        )

        response.code = 200
        response.msg = "绑定成功"

    return response



@csrf_exempt
def user_gongzhonghao_auth_oper(request,oper_type):
    response = Response.ResponseObj()

    if request.method == "GET":
        if oper_type == 'binding':
            print('request.GET -->', request.GET)

            forms_obj = LoginBindingForm(request.GET)
            if forms_obj.is_valid():

                # source = forms_obj.cleaned_data.get('source')  # 1,代表扫码,2 代表转发

                article_id = forms_obj.cleaned_data.get('article_id')  # 小程序用户ID
                customer_id = forms_obj.cleaned_data.get('user_id')    # 小程序用户ID
                level = forms_obj.cleaned_data.get('level')  # 小程序用户ID
                parent_id =forms_obj.cleaned_data.get('pid')  # 所属的父级的客户ID，为空代表直接扫码企业用户的二维码过来的。

                article_to_customer_belonger_obj = models.zgld_article_to_customer_belonger.objects.filter(
                    article_id=article_id,
                    customer_id=customer_id,
                    # customer_parent_id=parent_id
                )

                if article_to_customer_belonger_obj:
                    response.code = 302
                    response.msg = "文章和客户关系存在"

                else:
                    models.zgld_article_to_customer_belonger.objects.create(
                        article_id=article_id,
                        customer_id=customer_id,
                        customer_parent_id=parent_id,
                        level=level,
                    )

                    response.code = 200
                    response.msg = "绑定成功"


            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

    else:
        response.code = 402
        response.msg = "请求方式异常"

    return JsonResponse(response.__dict__)

