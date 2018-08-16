from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import requests
from zhugeleida.public.crypto_.WXBizMsgCrypt import WXBizMsgCrypt
import json
import redis
import xml.etree.cElementTree as ET
from django import forms
import datetime
from django.conf import settings
import os
from zhugeleida.forms.admin.dai_xcx_verify import CommitCodeInfoForm,SubmitAuditForm,GetqrCodeForm,GetLatestAuditForm,GetAuditForm



@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def dai_xcx_oper(request, oper_type):
    response = Response.ResponseObj()
    rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)
    if request.method == "POST":

        # 第三方代小程序上传
        if oper_type == 'code_commit_audit':

            # user_id = request.GET.get('user_id')
            '''
            ext.json  指导文件 https://developers.weixin.qq.com/miniprogram/dev/devtools/ext.html
                      extEnable	Boolean	 是	配置ext.json 是否生效
                      extAppid	String	 是	配置 授权方Appid
                      directCommit	Boolean	否	是否直接提交到待审核列表
                      {
                          "extEnable": true,
                          "extAppid": "wxf9c4501a76931b33",
                          "directCommit": false,
                      }
                      
            app.json  全局配置文件  https://developers.weixin.qq.com/miniprogram/dev/framework/config.html
            
            '''

            forms_obj = CommitCodeInfoForm(request.POST)
            if forms_obj.is_valid():
                user_id = request.GET.get('user_id')  # 账户
                app_ids_list = forms_obj.cleaned_data.get('app_ids_list')  # 账户
                user_version = forms_obj.cleaned_data.get('user_version') # 版本
                template_id = forms_obj.cleaned_data.get('template_id')   #模板ID
                user_desc = forms_obj.cleaned_data.get('user_desc')       #描述
                # ext_json = forms_obj.cleaned_data.get('ext_json')
                app_ids_list = json.loads(app_ids_list)
                objs = models.zgld_xiaochengxu_app.objects.filter(id__in=app_ids_list)
                if objs:
                    for obj in objs:
                        authorizer_refresh_token = obj.authorizer_refresh_token
                        authorizer_appid = obj.authorization_appid

                        ext_json = json.loads(obj.ext_json)
                        ext_json['extAppid'] = authorizer_appid
                        ext_json['ext'] = {
                            'company_id': obj.company_id
                        }

                        user_version = user_version
                        template_id = template_id

                        # ext_json = {
                        #     'extEnable': 'true',
                        #     'extAppid': authorizer_appid,
                        #     'directCommit': 'false',
                        # }
                        # app_id = 'wx67e2fde0f694111c'
                        # app_secret = '4a9690b43178a1287b2ef845158555ed'


                        key_name = '%s_authorizer_access_token' % (authorizer_appid)
                        authorizer_access_token = rc.get(key_name)  # 不同的 小程序使用不同的 authorizer_access_token，缓存名字要不一致。

                        if not authorizer_access_token:
                            data = {
                                'key_name': key_name,
                                'authorizer_refresh_token' : authorizer_refresh_token,
                                'authorizer_appid' : authorizer_appid
                            }
                            authorizer_access_token_result = create_authorizer_access_token(data)
                            if authorizer_access_token_result.code == 200:
                                authorizer_access_token = response.data
                            else:
                                return JsonResponse(authorizer_access_token.__dict__)


                        print('------ 第三方自定义的配置 ext_json ------>',json.dumps(ext_json))
                        get_wxa_commit_data =  {
                            'access_token': authorizer_access_token
                        }

                        post_wxa_commit_data = {
                            'template_id': template_id,        # 代码库中的代码模版ID
                            'ext_json': json.dumps(ext_json),  # 第三方自定义的配置
                            'user_version': user_version,      # 代码版本号，开发者可自定义
                            'user_desc': user_desc  # 代码描述，开发者可自定义
                        }

                        commit_url = 'https://api.weixin.qq.com/wxa/commit'
                        wxa_commit_info_ret = requests.post(commit_url, params=get_wxa_commit_data, data=json.dumps(post_wxa_commit_data))

                        wxa_commit_info_ret = wxa_commit_info_ret.json()
                        print('--------为授权的小程序帐号上传小程序代码 接口返回---------->>',wxa_commit_info_ret)

                        errcode = wxa_commit_info_ret.get('errcode')
                        errmsg = wxa_commit_info_ret.get('errmsg')
                        datetime_now = datetime.datetime.now()
                        if errcode == 0:
                            upload_code_obj = models.zgld_xiapchengxu_upload_audit.objects.create(
                                app_id=obj.id,
                                publisher_id=user_id,
                                desc=user_desc,
                                version_num=user_version,
                                template_id=template_id,
                                upload_code_date=datetime_now
                            )
                            # response.code = 200
                            # response.msg = '小程序帐号上传小程序代码成功'
                            print('------ 代小程序上传代码成功 ------>>')
                        else:
                            response.code = errcode
                            response.msg = errmsg  # https://open.weixin.qq.com/cgi-bin/showdocument?action=dir_list&t=resource/res_list&verify=1&id=open1489140610_Uavc4&token=&lang=zh_CN
                            return  JsonResponse(response.__dict__)

                        get_qrcode_url = 'https://api.weixin.qq.com/wxa/get_qrcode'
                        # app_id = forms_obj.cleaned_data.get('app_id')  # 账户
                        # upload_code_id = forms_obj.cleaned_data.get('upload_code_id')


                        authorizer_refresh_token = obj.authorizer_refresh_token
                        authorizer_appid = obj.authorization_appid

                        key_name = '%s_authorizer_access_token' % (authorizer_appid)
                        authorizer_access_token = rc.get(key_name)  # 不同的 小程序使用不同的 authorizer_access_token，缓存名字要不一致。

                        if not authorizer_access_token:
                            data = {
                                'key_name': key_name,
                                'authorizer_refresh_token': authorizer_refresh_token,
                                'authorizer_appid': authorizer_appid
                            }
                            authorizer_access_token_result = create_authorizer_access_token(data)
                            if authorizer_access_token_result.code == 200:
                                authorizer_access_token = response.data
                            else:
                                return JsonResponse(authorizer_access_token.__dict__)
                        path = 'pages/mingpian/index?uid=1&source=1'
                        get_qrcode_data = {
                            'access_token': authorizer_access_token,
                            'path': path,
                        }

                        get_qrcode_ret = requests.get(get_qrcode_url, params=get_qrcode_data)

                        try:

                            now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                            BASE_DIR = os.path.join(settings.BASE_DIR, 'statics', 'zhugeleida', 'imgs', 'admin', 'qr_code')

                            qr_code_name = '/%s_%s_QRCode.jpg' % (authorizer_appid, now_time)

                            path_qr_code_name = BASE_DIR + qr_code_name
                            qr_url = 'statics/zhugeleida/imgs/admin/qr_code%s' % (qr_code_name)

                            with open(path_qr_code_name, 'wb') as f:
                                f.write(get_qrcode_ret.content)

                            # response.code = 200
                            # response.msg = '生成并获取小程序体验码成功'
                            print('---------生成并获取小程序体验码成功--------->>',qr_url)
                            # response.data = {
                            #     'qrcode_url': qr_url
                            #
                            # }
                            upload_code_obj.experience_qrcode=qr_url
                            upload_code_obj.save()

                        except Exception as e:
                            response.code = 301
                            response.msg = '小程序的体验二维码_接口返回-错误'
                            print('------- 获取体验小程序的体验二维码_接口返回-错误 ---->>', get_qrcode_ret.text, '|', e)
                            return JsonResponse(response.__dict__)


                        authorizer_refresh_token = obj.authorizer_refresh_token
                        authorizer_appid = obj.authorization_appid

                        key_name = '%s_authorizer_access_token' % (authorizer_appid)
                        authorizer_access_token = rc.get(key_name)  # 不同的 小程序使用不同的 authorizer_access_token，缓存名字要不一致。

                        if not authorizer_access_token:
                            data = {
                                'key_name': key_name,
                                'authorizer_refresh_token': authorizer_refresh_token,
                                'authorizer_appid': authorizer_appid
                            }
                            authorizer_access_token_result = create_authorizer_access_token(data)
                            if authorizer_access_token_result.code == 200:
                                authorizer_access_token = response.data
                            else:
                                return JsonResponse(authorizer_access_token.__dict__)

                        # 获取小程序的第三方提交代码的页面配置
                        get_page_url = 'https://api.weixin.qq.com/wxa/get_page'
                        get_page_data = {
                            'access_token': authorizer_access_token,
                        }
                        page_data_ret = requests.get(get_page_url, params=get_page_data)
                        page_data_ret = page_data_ret.json()
                        errcode = page_data_ret.get('errcode')
                        errmsg = page_data_ret.get('errmsg')
                        page_list = page_data_ret.get('page_list')

                        print('-------- 第三方提交代码的页面配置 page_data_ret 返回------>>', page_data_ret)
                        if errcode == 0:

                            print('-----page_list--->>', page_list)
                            #-----page_list--->> ['pages/index/index', 'pages/logs/logs']


                        else:
                            response.code = errcode
                            response.msg = '获取第三方-页面配置报错: %s' % (errmsg)
                            return JsonResponse(response.__dict__)

                        # 获取授权小程序帐号的可选类目
                        get_category_url = 'https://api.weixin.qq.com/wxa/get_category'
                        get_category_data = {
                            'access_token': authorizer_access_token,
                        }
                        page_category_ret = requests.get(get_category_url, params=get_category_data)
                        page_category_ret = page_category_ret.json()
                        errcode = page_category_ret.get('errcode')
                        errmsg = page_category_ret.get('errmsg')
                        category_list = page_category_ret.get('category_list')

                        print('-------- 获取授权小程序帐号的可选类目 page_category_ret 返回------>>', page_category_ret)
                        if errcode == 0:
                            print('----- 可选类目 category_list--->>', category_list)
                            # -----category_list--->> [{'first_class': 'IT科技', 'second_class': '硬件与设备', 'first_id': 210, 'second_id': 211}]
                            response.code = 200
                            response.msg = '提交审核代码成功'

                        else:
                            response.code = errcode
                            response.msg = '获取第三方-页面配置报错: %s' % (errmsg)
                            return JsonResponse(response.__dict__)

                        submit_audit_url = 'https://api.weixin.qq.com/wxa/submit_audit'
                        item_list = []

                        # -----page_list--->> ['pages/index/index', 'pages/logs/logs']
                        item_dict = {
                            'address': page_list[0],
                            'first_class': category_list[0].get('first_class'),
                            'second_class' : category_list[0].get('second_class'),
                            'first_id': category_list[0].get('first_id'),
                            'second_id': category_list[0].get('second_id'),
                            'tag': '名片',
                            'title': '名片'
                        }

                        item_list.append(item_dict)

                        '''
                        {'errcode': 0, 'errmsg': 'ok', 'page_list': ['pages/index/index', 'pages/logs/logs'] }
        
                        {'errcode': 0, 'errmsg': 'ok', 
                             'category_list': [{
                                    "first_class":"教育",
                                    "second_class":"学历教育",
                                    "third_class":"高等",
                                    "first_id":3,
                                    "second_id":4,
                                    "third_id":5
                                }]
                             }
        
                        '''

                        get_submit_audit_data = {
                            'access_token': authorizer_access_token,
                        }
                        post_submit_audit_data = {
                            'item_list': item_list
                        }
                        post_submit_audit_data = json.dumps(post_submit_audit_data, ensure_ascii=False)
                        print('json.dumps(post_submit_audit_data)----->>',post_submit_audit_data)

                        submit_audit_ret = requests.post(submit_audit_url, params=get_submit_audit_data,
                                                        data=post_submit_audit_data.encode('utf-8'))

                        submit_audit_ret = submit_audit_ret.json()
                        auditid = submit_audit_ret.get('auditid')
                        errcode = submit_audit_ret.get('errcode')
                        errmsg = submit_audit_ret.get('errmsg')
                        now_time = datetime.datetime.now()
                        print('-------- 代码包-提交审核 返回 submit_audit_ret 返回------>>', submit_audit_ret)
                        if errcode == 0:

                            print('-----auditid--->>', auditid)
                            audit_result = 2  # (2,'审核中')
                            reason  = ''
                            response.code = 200
                            response.msg = '提交审核代码成功'

                        else:

                            audit_result = 3   # (3,'提交审核失败')
                            response.code = errcode
                            reason = '提交审核代码报错: %s : %s' % (errcode,errmsg)
                            response.msg = reason


                        upload_code_obj.auditid = auditid
                        upload_code_obj.audit_commit_date = now_time
                        upload_code_obj.audit_result = audit_result  # (2,'审核中')
                        upload_code_obj.reason = reason  # (2,'审核中')
                        upload_code_obj.save()

                else:
                    print("验证不通过")
                    response.code = 301
                    response.msg = json.loads(forms_obj.errors.as_json())

        # 获取体验小程序的体验二维码
        elif oper_type == 'get_qrcode':
            forms_obj = GetqrCodeForm(request.POST)

            if forms_obj.is_valid():
                pass

        # 将第三方提交的代码包提交审核
        elif oper_type == 'submit_audit':
            forms_obj = SubmitAuditForm(request.POST)
            if forms_obj.is_valid():
                pass

        return JsonResponse(response.__dict__)

    elif request.method == "GET":
        print('------post.get--->',)
        #查询最新一次提交的审核状态
        if oper_type == 'get_latest_audit_status':
            # forms_obj = GetLatestAuditForm(request.POST)
            # if forms_obj.is_valid():

            objs = models.zgld_xiapchengxu_upload_audit.objects.filter(audit_result=2,auditid__isnull=False)

            if objs: #如果在审核中，并有编号，说明提交了审核。定时器要不停的去轮训,一旦发现有通过审核的，就要触发上线操作,并记录下来。
                auditid = objs[0].auditid
                for obj in objs:

                    app_id = obj.app_id
                    get_latest_auditstatus_url = 'https://api.weixin.qq.com/wxa/get_latest_auditstatus'
                    # app_id = forms_obj.cleaned_data.get('app_id')  # 账户
                    # audit_code_id= forms_obj.cleaned_data.get('audit_code_id')

                    # app_obj = models.zgld_xiaochengxu_app.objects.get(id=app_id)
                    authorizer_refresh_token = obj.app.authorizer_refresh_token
                    authorizer_appid = obj.app.authorization_appid

                    key_name = '%s_authorizer_access_token' % (authorizer_appid)
                    authorizer_access_token = rc.get(key_name)  #不同的 小程序使用不同的 authorizer_access_token，缓存名字要不一致。

                    if not authorizer_access_token:
                        data = {
                            'key_name': key_name,
                            'authorizer_refresh_token': authorizer_refresh_token,
                            'authorizer_appid': authorizer_appid
                        }
                        authorizer_access_token_result = create_authorizer_access_token(data)
                        if authorizer_access_token_result.code == 200:
                            authorizer_access_token = response.data
                        else:
                            return JsonResponse(authorizer_access_token.__dict__)

                    get_latest_audit_data = {
                        'access_token': authorizer_access_token
                    }

                    get_latest_audit_ret = requests.get(get_latest_auditstatus_url, params=get_latest_audit_data)
                    now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    get_latest_audit_ret = get_latest_audit_ret.json()
                    print('------获取查询审核中+最新一次提交的审核状态 接口返回----->>',get_latest_audit_ret)

                    errcode = get_latest_audit_ret.get('errcode')
                    errmsg = get_latest_audit_ret.get('errmsg')
                    status = get_latest_audit_ret.get('status')
                    reason = get_latest_audit_ret.get('reason')

                    if status == 0:
                        response.code = 200
                        response.msg = '审核成功ID'
                        print('--------审核成功ID | audit_code_id: -------->',obj.app_id,'|',auditid)
                        release_obj = models.zgld_xiapchengxu_release.objects.filter(audit_code_id=obj.app_id)
                        obj.audit_reply_date = now_time

                        if not release_obj: # 没有发布相关的代码记录,说明没有上过线呢。
                            release_url =  'https://api.weixin.qq.com/wxa/release'
                            get_release_data = {
                                'access_token': authorizer_access_token
                            }

                            get_release_ret = requests.post(release_url, params=get_release_data)
                            get_release_ret = get_release_ret.json()
                            errcode = get_release_ret.get('errcode')
                            errmsg = get_release_ret.get('errmsg')
                            status = get_release_ret.get('status')
                            reason = get_release_ret.get('reason')

                            if errcode == 0:
                                release_result=1  # 上线成功
                                reason = ''
                                print('--------发布已通过审核的小程序【成功】: auditid | audit_code_id -------->>',auditid,'|',obj.app_id)

                            else:
                                release_result=2  # 上线失败
                                if errcode == -1:
                                   reason = '系统繁忙'
                                elif errcode ==  85019:
                                   reason = '没有审核版本'
                                elif errcode == 85020:
                                    reason = '审核状态未满足发布'
                                print('-------发布已通过审核的小程序【失败】auditid | audit_code_id -------->>',auditid,'|' ,obj.app_id)


                            models.zgld_xiapchengxu_release.objects.create(
                                app=app_id,
                                audit_code_id=obj.app_id,
                                release_result =release_result,
                                release_commit_date=now_time,
                                reason=reason
                            )



                    elif status == 1: # 0为审核成功
                        response.code = 200
                        response.msg = '审核状态失败'


                    elif status == 2 :
                        response.code = 200
                        response.msg = '审核中'


                    obj.audit_result = status
                    obj.reason = reason
                    obj.save()

                # else:
                #     print("--验证不通过-->",forms_obj.errors.as_json())
                #     response.code = 301
                #     response.msg = json.loads(forms_obj.errors.as_json())
            else:
                response.code = 302
                response.msg = '没有正在审核中的代码'
                print('-------- 没有正在【审核中】状态的代码 ------>>')

        #查询某个指定版本的审核状态
        elif oper_type == 'get_auditstatus':
            forms_obj = GetAuditForm(request.POST)

            if forms_obj.is_valid():

                get_auditstatus_url = 'https://api.weixin.qq.com/wxa/get_auditstatus'
                app_id = forms_obj.cleaned_data.get('app_id')  # 账户
                audit_code_id= forms_obj.cleaned_data.get('audit_code_id')

                obj = models.zgld_xiaochengxu_app.objects.get(id=app_id)
                authorizer_refresh_token = obj.authorizer_refresh_token
                authorizer_appid = obj.authorization_appid

                key_name = '%s_authorizer_access_token' % (authorizer_appid)
                authorizer_access_token = rc.get(key_name)  # 不同的 小程序使用不同的 authorizer_access_token，缓存名字要不一致。

                if not authorizer_access_token:
                    data = {
                        'key_name': key_name,
                        'authorizer_refresh_token': authorizer_refresh_token,
                        'authorizer_appid': authorizer_appid
                    }
                    authorizer_access_token_result = create_authorizer_access_token(data)
                    if authorizer_access_token_result.code == 200:
                        authorizer_access_token = response.data
                    else:
                        return JsonResponse(authorizer_access_token.__dict__)

                obj = models.zgld_xiapchengxu_upload_audit.objects.get(id=audit_code_id)

                if obj:

                    auditid = obj.auditid
                    get_audit_data = {
                        'access_token': authorizer_access_token
                    }
                    post_audit_data = {
                        'auditid': auditid
                    }

                    get_audit_ret = requests.post(get_auditstatus_url,params=get_audit_data,data=post_audit_data )
                    now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    get_audit_ret = get_audit_ret.json()
                    errcode = get_audit_ret.get('errcode')
                    reason = get_audit_ret.get('reason')
                    status = get_audit_ret.get('status')
                    if status == 0:
                        response.code = 200
                        response.msg = '审核状态成功'

                    elif status == 1: # 0为审核成功
                        response.code = 200
                        response.msg = '审核状态失败'

                    elif status == 2 :
                        response.code = 200
                        response.msg = '审核中'

                    obj.audit_result = status
                    obj.reason=reason
                    obj.save()

                else:
                    print("--验证不通过-->",forms_obj.errors.as_json())
                    response.code = 301
                    response.msg = json.loads(forms_obj.errors.as_json())


    return JsonResponse(response.__dict__)





def create_authorizer_access_token(data):
    response = Response.ResponseObj()
    authorizer_appid = data.get('authorizer_appid')
    authorizer_refresh_token = data.get('authorizer_refresh_token')
    key_name = data.get('key_name')

    app_id = 'wx67e2fde0f694111c'
    app_secret = '4a9690b43178a1287b2ef845158555ed'
    rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)

    component_access_token = rc.get('component_access_token')
    if not component_access_token:

        get_pre_auth_data = {}
        post_component_data = {}
        post_component_data['component_appid'] = app_id
        post_component_data['component_appsecret'] = app_secret
        component_verify_ticket = rc.get('ComponentVerifyTicket')
        post_component_data['component_verify_ticket'] = component_verify_ticket

        post_component_url = 'https://api.weixin.qq.com/cgi-bin/component/api_component_token'
        component_token_ret = requests.post(post_component_url, data=json.dumps(post_component_data))
        print('--------- 获取第三方平台 component_token_ret.json --------->>', component_token_ret.json())
        component_token_ret = component_token_ret.json()
        access_token = component_token_ret.get('component_access_token')
        if access_token:
            get_pre_auth_data['component_access_token'] = access_token
            rc.set('component_access_token', access_token, 7000)
            component_access_token = access_token

        else:
            response.code = 400
            response.msg = "-------- 获取第三方平台 component_token_ret 返回错误 ------->"
            return JsonResponse(response.__dict__)


    get_auth_token_data = {
        'component_access_token': component_access_token
    }

    post_auth_token_data = {
        'component_appid': app_id,
        'authorizer_appid': authorizer_appid,
        'authorizer_refresh_token': authorizer_refresh_token
    }

    authorizer_token_url = 'https://api.weixin.qq.com/cgi-bin/component/api_authorizer_token'
    authorizer_info_ret = requests.post(authorizer_token_url, params=get_auth_token_data,
                                        data=json.dumps(post_auth_token_data))
    authorizer_info_ret = authorizer_info_ret.json()

    print('-------获取（刷新）授权小程序的接口调用凭据 authorizer_token 返回--------->>', authorizer_info_ret)

    authorizer_access_token = authorizer_info_ret.get('authorizer_access_token')
    authorizer_refresh_token = authorizer_info_ret.get('authorizer_refresh_token')

    if authorizer_access_token and authorizer_refresh_token:
        rc.set(key_name, authorizer_access_token, 7000)
        response.code = 200
        response.msg = "获取令牌成功"
        response.data = authorizer_access_token
        print('------ 获取令牌（authorizer_access_token）成功------>>',authorizer_access_token)

    else:
        print('------ 获取令牌（authorizer_access_token）为空------>>')
        response.code = 400
        response.msg = "获取令牌authorizer_access_token为空"
        return JsonResponse(response.__dict__)

    return  response


def create_component_access_token():
    response = Response.ResponseObj()

    app_id = 'wx67e2fde0f694111c'
    app_secret = '4a9690b43178a1287b2ef845158555ed'
    rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)

    component_access_token = rc.get('component_access_token')
    if not component_access_token:

        get_pre_auth_data = {}
        post_component_data = {}
        post_component_data['component_appid'] = app_id
        post_component_data['component_appsecret'] = app_secret
        component_verify_ticket = rc.get('ComponentVerifyTicket')
        post_component_data['component_verify_ticket'] = component_verify_ticket

        post_component_url = 'https://api.weixin.qq.com/cgi-bin/component/api_component_token'
        component_token_ret = requests.post(post_component_url, data=json.dumps(post_component_data))
        print('--------- 获取第三方平台 component_token_ret.json --------->>', component_token_ret.json())
        component_token_ret = component_token_ret.json()
        access_token = component_token_ret.get('component_access_token')
        if access_token:
            get_pre_auth_data['component_access_token'] = access_token
            rc.set('component_access_token', access_token, 7000)
            component_access_token = access_token

        else:
            response.code = 400
            response.msg = "-------- 获取第三方平台 component_token_ret 返回错误 ------->"
            return JsonResponse(response.__dict__)

    return    component_access_token

