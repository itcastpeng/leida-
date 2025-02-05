from django.shortcuts import render, redirect
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.smallprogram_verify import SmallProgramAddForm, LoginBindingForm

import time,os
import datetime

import requests
from publicFunc.condition_com import conditionCom
from ..conf import *
from zhugeapi_celery_project import tasks
from zhugeleida.public.common import action_record
import base64
import json
import redis
from collections import OrderedDict
import logging.handlers
from zhugeleida.views_dir.admin.dai_xcx import create_component_access_token


# 从微信小程序接口中获取openid等信息
def get_openid_info(get_token_data):
    appurl = 'https://api.weixin.qq.com/sns/component/jscode2session'

    s = requests.session()
    s.keep_alive = False  # 关闭多余连接
    ret = s.get(appurl, params=get_token_data)

    # ret = requests.get(appurl, params=get_token_data)
    ret_json = ret.json()
    print('------ 第三方平台 代替小程序实现【登录功能】接口返回 ----->>', ret_json)

    openid = ret_json.get('openid')  # 用户唯一标识
    session_key = ret_json.get('session_key')  # 会话密钥

    ret_data = {
        'openid': openid,
        'session_key': session_key
    }

    return ret_data


@csrf_exempt
def login(request):
    response = Response.ResponseObj()

    if request.method == "GET":
        print('-------【小程序登录啦】 request.GET 数据是: ------->', request.GET)
        version_num = request.GET.get('user_version')

        forms_obj = SmallProgramAddForm(request.GET)
        if forms_obj.is_valid():
            js_code = forms_obj.cleaned_data.get('code')
            code_objs = models.save_code.objects.filter(code=js_code)
            if not code_objs:
                models.save_code.objects.create(code=js_code)
                user_type = forms_obj.cleaned_data.get('user_type')
                company_id = forms_obj.cleaned_data.get('company_id')
                user_id = forms_obj.cleaned_data.get('uid')
                xcx_type = request.GET.get('xcx_type') # 是否是米扬丽格

                company_id = int(company_id) if company_id else ''

                is_release_version_num = True
                if xcx_type == 'case_type' and not company_id: # 案例类型的话
                    company_id = 13
                    is_release_version_num = False
                    print('--------- [没有company_id], ext里没有company_id或小程序审核者自己生成的体验码 。 uid | company_id(默认) 是： -------->>',
                          user_id, company_id)


                elif not company_id:  # 说明 ext里没有company_id 此时要让它看到默认公司。。
                    # 注意的是小程序审核者 ，生成的体验码，既没有UID，也没有 company_id ，所以 需要默认的处理下。
                    company_id = 1
                    is_release_version_num = False
                    print('--------- [没有company_id], ext里没有company_id或小程序审核者自己生成的体验码 。 uid | company_id(默认) 是： -------->>',user_id, company_id)



                app_objs = models.zgld_xiaochengxu_app.objects.filter(company_id=company_id)
                services_type = app_objs[0].three_services_type
                three_services_type = ''
                if services_type == 1:     # (1, '小程序(名片版)第三方平台'),
                    three_services_type=3

                elif services_type == 2:   # (2, '小程序(案例库)第三方平台')
                    three_services_type=4

                component_appid = ''
                three_service_objs = models.zgld_three_service_setting.objects.filter(three_services_type=three_services_type)  # 小程序
                if three_service_objs:
                    three_service_obj = three_service_objs[0]
                    qywx_config_dict = three_service_obj.config
                    if qywx_config_dict:
                        qywx_config_dict = json.loads(qywx_config_dict)

                    component_appid = qywx_config_dict.get('app_id')

                else:
                    print('------ 【公众号第三方-无配置信息】component_appid ------>>')

                obj = models.zgld_xiaochengxu_app.objects.get(company_id=company_id)
                authorizer_appid = obj.authorization_appid
                # component_appid = 'wx67e2fde0f694111c'

                # if  version_num: # 有版本号(从ext 里读取的)
                online_version_num = obj.version_num
                print('---- Ext里的版本号: ---->',version_num)

                if version_num != online_version_num:  # ext 里的版本号是否等于目前已经上线的版本号，如果相等代表已经发布同步，不必隐藏转发按钮
                    is_release_version_num = False  # 不相等说明要隐藏按钮。
                    print('-------- 公司ID:%s | online版本号:%s | ext里的版本号:%s ------------->>',
                          (company_id, online_version_num, version_num))

                component_access_token = create_component_access_token(company_id)
                get_token_data = {
                    'appid': authorizer_appid,  # 授权小程序的AppID
                    'js_code': js_code,  # 登录时获取的 code
                    'grant_type': 'authorization_code',
                    'component_appid': component_appid,  # 第三方平台appid
                    'component_access_token': component_access_token  # 第三方平台的 component_access_token
                }

                ret_data = get_openid_info(get_token_data)
                openid = ret_data['openid']
                session_key = ret_data['session_key']

                customer_objs = models.zgld_customer.objects.filter(
                    openid=openid,
                    user_type=user_type
                )
                # 如果openid存在一条数据
                if customer_objs:
                    token = customer_objs[0].token
                    client_id = customer_objs[0].id
                    customer_objs.update(
                        session_key= session_key
                    )

                else:
                    token = account.get_token(account.str_encrypt(openid))
                    obj = models.zgld_customer.objects.create(
                        session_key=session_key,
                        company_id=company_id,
                        token=token,
                        openid=openid,
                        user_type=user_type,  # (1 代表'微信公众号'),  (2 代表'微信小程序'),
                        # superior=customer_id,  #上级人。
                    )

                    client_id = obj.id
                    print('---------- 【小程序】用户第一次注册、创建成功 | openid入库 -------->')

                if not user_id:  # 如果没有user_id 说明是搜索进来 或者 审核者自己生成的二维码。
                    user_customer_belonger_obj = models.zgld_user_customer_belonger.objects.filter(
                        customer_id=client_id,
                        user__company_id=company_id
                    ).order_by('-last_activity_time')
                    for i in user_customer_belonger_obj:
                        print('i.user.username--------> ', i.user.username)
                    if user_customer_belonger_obj:  # 上一次进入的咨询 后期登录还是该咨询
                        user_customer_obj = user_customer_belonger_obj[0]
                        user_id = user_customer_obj.user_id
                    else:
                        user_id = models.zgld_userprofile.objects.filter(company_id=company_id, status=1).order_by('?')[0].id
                    print('----------- [没有uid],说明是搜索进来或者审核者自己生成的二维码 。 company_id | uid ：------------>>', company_id, user_id)

                ret_data = {
                    'cid': client_id,
                    'token': token,
                    'uid': user_id,
                    'company_id': company_id,
                    'is_release_version_num': is_release_version_num
                }

                print('-------- 接口返回给【小程序】的数据 json.dumps(ret_data) ------------>>', json.dumps(ret_data))
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
@account.is_token(models.zgld_customer)
def login_oper(request, oper_type):
    response = Response.ResponseObj()

    if request.method == "GET":
        if oper_type == 'binding':
            print('=-----======================================*****************************************************************=================================')
            print('request.GET -->', request.GET)

            forms_obj = LoginBindingForm(request.GET)
            if forms_obj.is_valid():

                # user_type = forms_obj.cleaned_data.get('user_type')
                source = forms_obj.cleaned_data.get('source')  # 1,代表扫码,2 代表转发
                user_id = forms_obj.cleaned_data.get('uid')  # 所属的企业用户的ID
                customer_id = forms_obj.cleaned_data.get('user_id')  # 小程序用户ID
                parent_id = request.GET.get('pid', '')  # 所属的父级的客户ID，为空代表直接扫码企业用户的二维码过来的。
                user_objs = models.zgld_userprofile.objects.select_related('company').filter(id=user_id)
                if user_objs:
                    company_id = user_objs[0].company_id
                    is_customer_unique = user_objs[0].company.is_customer_unique

                    print('--is_customer_unique------is_customer_unique------------is_customer_unique--', is_customer_unique)
                    if is_customer_unique:  # 唯一性

                        user_customer_belonger_obj = models.zgld_user_customer_belonger.objects.filter(customer_id=customer_id,
                                                                                               user__company_id=company_id)
                    else:
                        user_customer_belonger_obj = models.zgld_user_customer_belonger.objects.filter(customer_id=customer_id,user_id=user_id)

                    if user_customer_belonger_obj:
                        response.code = 302
                        response.msg = "关系存在"
                        print('关系存在------------------------关系存在----------------------关系存在------------------------关系存在')

                    else:
                        print('--------关系不存在创建-------------------------关系不存在创建-------------------关系不存在创建----------------------关系不存在创建')
                        if not source or source == 'undefined':
                            source = 1

                        print('值 source------->>',source)
                        print('值 customer_id------->>', customer_id)
                        print('值 user_id------->>', user_id)

                        obj = models.zgld_user_customer_belonger.objects.create(customer_id=customer_id, user_id=user_id,
                                                                                source=source)
                        obj.customer_parent_id = parent_id  # 上级人。
                        obj.save()

                        user_obj = models.zgld_userprofile.objects.get(id=user_id)
                        company_id = user_obj.company_id
                        objs = models.zgld_customer.objects.filter(
                            id=customer_id,
                        )
                        if objs:
                            objs.update(company_id=company_id)

                        # 插入第一条用户和客户的对话信息
                        msg = '您好,我是%s的%s,欢迎进入我的名片,有什么可以帮到您的吗?您可以在这里和我及时沟通。' % (obj.user.company.name, obj.user.username)
                        # models.zgld_chatinfo.objects.create(send_type=1, userprofile_id=user_id, customer_id=customer_id,
                        #                                     msg=msg)

                        _content = { 'info_type': 1 }
                        encodestr = base64.b64encode(msg.encode('utf-8'))
                        msg = str(encodestr, 'utf-8')
                        _content['msg'] = msg
                        content = json.dumps(_content)

                        models.zgld_chatinfo.objects.create(send_type=1, userprofile_id=user_id, customer_id=customer_id,content=content,msg=int(time.time()))

                        print('---------- 插入 第一条用户和客户的对话信息 successful ---->')

                        rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)

                        redis_user_id_key = 'message_user_id_{uid}'.format(uid=user_id)
                        redis_customer_id_key = 'message_customer_id_{cid}'.format(cid=customer_id)
                        # redis_customer_query_info_key = 'message_customer_id_{cid}_info_num'.format(cid=customer_id)

                        redis_user_query_info_key = 'message_user_id_{uid}_info_num'.format(
                            uid=user_id)  # 小程序发过去消息,雷达用户的key 消息数量发生变化
                        redis_user_query_contact_key = 'message_user_id_{uid}_contact_list'.format(
                            uid=user_id)  # 小程序发过去消息,雷达用户的key 消息列表发生变化

                        rc.set(redis_user_id_key, True)
                        rc.set(redis_customer_id_key, True)
                        # rc.set(redis_customer_query_info_key, True)  # 通知公众号文章客户消息数量变化了

                        rc.set(redis_user_query_info_key, True)  # 代表 雷达用户 消息数量发生了变化
                        rc.set(redis_user_query_contact_key, True)  # 代表 雷达用户 消息列表的数量发生了变化


                        # 异步生成小程序和企业用户对应的小程序二维码
                        data_dict = {'user_id': user_id, 'customer_id': customer_id}
                        tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))  #



                        response.code = 200
                        response.msg = "绑定关系成功"
                else:
                    response.code = 301
                    response.msg = '用户不存在'
            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())




    else:
        if oper_type == 'send_user_info':
            # 前端把小程序授权的用户信息入库。
            customer_id = request.GET.get('user_id')
            uid = request.GET.get('uid') # 用户ID
            headimgurl = request.POST.get('avatarUrl')
            city = request.POST.get('city')
            country = request.POST.get('country')
            province = request.POST.get('province')

            gender = request.POST.get('gender')  # 1代表男
            language = request.POST.get('language')
            username = request.POST.get('nickName')
            # formid =  request.POST.get('formId')
            page_info = int(request.POST.get('page')) if request.POST.get('page') else ''

            # LOG_FILE = r'test.log'
            # handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes= 500 *1024 * 1024, backupCount=2, encoding='utf-8')  # 实例化handler
            # fmt = '%(asctime)s - %(levelname)s - %(message)s'

            # formatter = logging.Formatter(fmt)  # 实例化formatter
            # handler.setFormatter(formatter)  # 为handler添加formatter
            #
            # logger = logging.getLogger('test')  # 获取名为tst的logger
            # logger.addHandler(handler)  # 为logger添加handler

            # logger.debug(log_info)

            encodestr = base64.b64encode(username.encode('utf-8'))
            customer_name = str(encodestr, 'utf-8')

            # logger.setLevel(logging.DEBUG)
            # log_info = "request.GET==> %s | b64encode:%s |request.POST==> %s" % (request.GET,customer_name,request.POST)
            # logger.info(log_info)

            objs = models.zgld_customer.objects.filter(
                id=customer_id,
            )
            if objs:
                objs.update(
                    username=customer_name,
                    headimgurl=headimgurl,
                    # formid = formid,
                    city=city,
                    country=country,
                    province=province,
                    language=language,
                )

                models.zgld_information.objects.create(
                    user_id=uid,
                    sex=gender,
                    customer_id=customer_id
                )

                # (1, '查看名片详情'),
                # (2, '查看产品列表'),
                # (3, '查看产品详情'),
                # (4, '查看官网'),
                username = base64.b64decode(objs[0].username)
                username = str(username, 'utf-8')

                remark = ''
                if page_info == 1:
                    remark = '已向您授权访问【名片详情】页面'

                elif page_info == 2:
                    remark = '已向您授权访问【产品列表】页面'

                elif page_info == 3:
                    remark = '已向您授权访问【商品详情】页面'

                elif page_info == 4:
                    remark = '已向您授权访问【公司官网】页面'

                elif page_info == 5: # 米扬丽格 首次访问雷达日记首页
                    remark = '已向您授权访问【日记首页】页面'

                elif page_info == 6: # 米扬丽格 首次访问雷达日记列表
                    remark = '已向您授权访问【日记详情】页面'

                data = request.GET.copy()
                print('data --> request.GET.copy() -->', data)
                data['action'] = 13  # 代表用客户授权访问
                data['uid'] = uid
                action_record(data, remark)

                response.data = {'ret_data': username + ' 已向您授权登录页面'}

                if headimgurl:
                    s = requests.session()
                    s.keep_alive = False  # 关闭多余连接
                    html = s.get(headimgurl)

                    now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    filename = "/xcx_cid_%s_%s.jpg" % (customer_id, now_time)
                    file_dir = os.path.join('statics', 'zhugeleida', 'imgs', 'xiaochengxu', 'user_photo') + filename
                    with open(file_dir, 'wb') as file:
                        file.write(html.content)

                    print('----- 生成 到本地头像 file_dir ---->>', file_dir)
                    objs.update(
                        headimgurl=file_dir
                    )



                response.code = 200
                response.msg = "保存成功"
            else:
                response.code = 301
                response.msg = "用户不存在"


        elif oper_type == 'send_form_id':
            formid = request.POST.get('formId')
            customer_id = request.GET.get('user_id')

            objs = models.zgld_customer.objects.filter(id=customer_id)

            if objs and formid and 'formId' not in formid:
                print('formid ------------------->', formid)

                exist_formid = objs[0].formid
                if not exist_formid:
                    exist_formid = "[]"

                exist_formid_json = json.loads(exist_formid)
                exist_formid_json.append(formid)
                now_form_id_json = list(set(exist_formid_json))

                # print('============ Exist_formid_json  now_form_id_list =====>>',exist_formid_json,'=====>','\n',now_form_id_json)
                objs.update(formid=json.dumps(now_form_id_json))

                response.code = 200
                response.msg = "保存成功"


    return JsonResponse(response.__dict__)


def bottom_button_info(request):
    response = Response.ResponseObj()

    if request.method == "GET":
        company_id = request.GET.get('company_id')
        version_num = request.GET.get('version_num')

        is_release_version_num = True
        if not company_id:  # 说明 ext里没有company_id 此时要让它看到默认公司。。
            # 注意的是小程序审核者 ，生成的体验码，既没有UID，也没有 company_id ，所以 需要默认的处理下。
            company_id = 1
            is_release_version_num = False


        buttom_navigation_data_list = [
            {
                "default_url": "icon_mingpian_01.png",
                "selected_url": "icon_mingpian_02.png",
                "to_url": "pages/mingpian/index",
                "text": "名片",
                "order": 1
            },
            {
                "default_url": "chat.png",
                "selected_url": "chat.png",
                "to_url": "pages/mingpian/msg",
                "text": "咨询",
                "order": 2
            },
            {
                "default_url": "icon_guanwang_01.png",
                "selected_url": "icon_guanwang_02.png",
                "to_url": "pages/guanwang/index",
                "text": "官网",
                "order": 4
            }
        ]
        obj = models.zgld_company.objects.get(id=company_id)
        shopping_type = obj.shopping_type   # 类型 产品/商城
        is_show_jszc = obj.is_show_jszc     # 是否展示技术支持
        shopping_info_dict = ''
        ret_data = {}

        _obj = models.zgld_xiaochengxu_app.objects.get(company_id=company_id)

        # if  version_num: # 有版本号(从ext 里读取的)
        online_version_num = _obj.version_num
        print('---- 按钮 Ext里的版本号: ---->', version_num)

        if version_num != online_version_num:  # ext 里的版本号是否等于目前已经上线的版本号，如果相等代表已经发布同步，不必隐藏转发按钮
            is_release_version_num = False  # 不相等说明要隐藏按钮。

        print('-------- 按钮 公司ID:%s | online版本号:%s | ext里的版本号:%s ------------->>',(company_id, online_version_num, version_num))


        is_open_mall = False  # 小程序是否展示商城
        if shopping_type == 1:  # 1、代表产品
            shopping_info_dict = {
                "default_url": "icon_chanpin_01.png",
                "selected_url": "icon_chanpin_02.png",
                "to_url": "pages/chanpin/index",
                "text": "产品",
                "order": 3
            }

        elif shopping_type == 2:  # 2、 代表商城
            is_open_mall = True
            shangChengName = ''
            _objs = models.zgld_shangcheng_jichushezhi.objects.filter(xiaochengxucompany_id=company_id)
            if _objs:
                _obj = _objs[0]
                shangChengName = _obj.shangChengName

            shopping_info_dict = {
                "default_url": "icon_store_01.png",
                "selected_url": "icon_store_02.png",
                "to_url": "pages/store/store",
                "text": "商城",
                "order": 3
            }
            ret_data['shangChengName'] = shangChengName

        if int(company_id) == 12: # 米扬丽格 案例版 首次点击咨询 授权手机号  小程序上线后使用is_first_authorization控制
            is_release_version_num = False

        if int(company_id) == 15:
            is_first_authorization = is_release_version_num
        else:
            is_first_authorization = False

        buttom_navigation_data_list.insert(2, shopping_info_dict)
        ret_data['buttom_navigation_data'] = buttom_navigation_data_list  # 按钮
        ret_data['shop_type'] = shopping_type
        ret_data['shop_type_text'] = obj.get_shopping_type_display()
        ret_data['is_show_jszc'] = is_show_jszc
        ret_data['is_show_jszc_text'] = obj.get_is_show_jszc_display()
        ret_data['is_release_version_num'] = is_release_version_num
        ret_data['is_open_mall'] = is_open_mall                         # 是否展示商城
        ret_data['is_first_authorization'] = is_first_authorization     # 案例版首次点击咨询是否授权

        print('-------- 按钮 接口返回给【小程序】的数据 json.dumps(ret_data) ------------>>', json.dumps(ret_data))
        response.code = 200
        response.msg = "返回成功"
        response.data = ret_data

    return JsonResponse(response.__dict__)


def login_oper_control(request):
    response = Response.ResponseObj()

    if request.method == "GET":
        mingan_info = {
            "mingpian" : {
                "mingpian1": "转发",
                "mingpian2": "转发到好友或群聊",
                "mingpian3": "生成名片海报"
            },
            "chanpin": {
                "chanpin1": "在线咨询",
                "chanpin2": "转发到朋友"
            },
            "poster"  : {
                "poster1" : "保存名片海报",
                "poster2" : "保存小程序码到相册便于二次进入该名片，便于分享到朋友圈。"
            },
            "button_msg": {
                "msg": "发送手机号"
            }

        }

        # mingan_info = json.dumps(mingan_info)
        response.code = 200
        response.data = mingan_info
        response.msg = "返回成功"

    return JsonResponse(response.__dict__)