from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import time
import datetime
from publicFunc.condition_com import conditionCom
from zhugeleida.forms.user_verify import UserAddForm, UserUpdateForm, UserSelectForm,ScanCodeToAddUserForm
import json
from ..conf import *
import requests
from  zhugeleida.views_dir.qiyeweixin.qr_code_auth import create_small_program_qr_code
from zhugeapi_celery_project import tasks
from django.db.models import Q
import redis
from zhugeleida.public.common import jianrong_create_qiyeweixin_access_token
from zhugeleida.public.WorkWeixinOper import WorkWeixinOper


# cerf  token验证
# 用户展示模块
@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def user(request):
    response = Response.ResponseObj()
    if request.method == "GET":
        forms_obj = UserSelectForm(request.GET)
        _type = request.GET.get('type')

        if forms_obj.is_valid():
            current_page = forms_obj.cleaned_data['current_page']
            length = forms_obj.cleaned_data['length']
            user_id = request.GET.get('user_id')
            print('--------------->>',request.GET)
            print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)
            order = request.GET.get('order', '-create_date')
            status = request.GET.get('status')

            field_dict = {
                'id': '',
                'username': '__contains',         #名称模糊搜索
                # 'company__name': '__contains',    #公司名称
                'position':  '__contains',        # 职位搜索
                'department':  '',                # 部门搜索，按ID
                'status':  '',                    # (1, "启用"),   (2, "未启用"),
                # 'last_login_date': ''
            }

            q = conditionCom(request, field_dict)
            # if status:
            #     q.add(Q(**{'status': int(status)}), Q.AND)

            print('------q------>>',q)
            admin_userobj = models.zgld_admin_userprofile.objects.get(id=user_id)
            role_id = admin_userobj.role_id
            company_id = admin_userobj.company_id

            # if role_id == 1:  # 超级管理员,展示出所有的企业用户
            #    pass
            #
            # else:  #管理员，展示出自己公司的用户
            q.add(Q(**{"company_id": company_id}), Q.AND)

            if _type != 'temp_user':
                objs = models.zgld_userprofile.objects.select_related('company').filter(q).order_by(order)

                count = objs.count()

                if length != 0:
                    start_line = (current_page - 1) * length
                    stop_line = start_line + length
                    objs = objs[start_line: stop_line]


                ret_data = []

                department_objs = models.zgld_department.objects.filter(company_id=company_id).values('id','name')
                department_list =  list(department_objs)  if department_objs else []

                if objs:
                    mingpian_available_num = objs[0].company.mingpian_available_num
                    for obj in objs:
                        print('oper_user_username -->', obj)

                        department = ''
                        department_id = []
                        departmane_objs = obj.department.all()
                        print('departmane_objs -->', departmane_objs)
                        if departmane_objs:
                            print('departmane_objs.values_list("name") -->', departmane_objs.values_list('name'))
                            department = ', '.join([i[0] for i in departmane_objs.values_list('name')])
                            department_id = [i[0] for i in departmane_objs.values_list('id')]


                        mingpian_avatar_obj = models.zgld_user_photo.objects.filter(user_id=obj.id, photo_type=2).order_by('-create_date')

                        mingpian_avatar = ''
                        if mingpian_avatar_obj:
                            mingpian_avatar =  mingpian_avatar_obj[0].photo_url
                        else:

                            if obj.avatar.startswith("http"):
                                mingpian_avatar = obj.avatar
                            else:
                                mingpian_avatar =  obj.avatar

                        ret_data.append({
                            'id': obj.id,
                            'userid': obj.userid,
                            'username': obj.username,
                            'create_date': obj.create_date,
                            'last_login_date': obj.last_login_date,
                            'position': obj.position,
                            'mingpian_phone': obj.mingpian_phone,  # 名片显示的手机号
                            'phone': obj.wechat_phone,          # 代表注册企业微信注册时的电话
                            'avatar': mingpian_avatar,          # 头像
                            'qr_code': obj.qr_code,
                            'company': obj.company.name,
                            'company_id': obj.company_id,
                            'department' : department,
                            'department_id' : department_id,
                            'gender': obj.gender,

                            'status': obj.status,
                            'status_text': obj.get_status_display(),
                            'boss_status': obj.boss_status,
                            'boss_status_text': obj.get_boss_status_display(),

                            'article_admin_status': obj.article_admin_status,
                            'article_admin_status_text': obj.get_article_admin_status_display()


                        })
                        #  查询成功 返回200 状态码
                    response.code = 200
                    response.msg = '查询成功'
                    response.data = {
                        'ret_data': ret_data,
                        'mingpian_available_num': mingpian_available_num,
                        'data_count': count,
                        'department_list' : department_list
                    }


                else:
                    response.code = 301
                    response.msg = "产品为空"

        else:
            response.code = 402
            response.msg = "请求异常"
            response.data = json.loads(forms_obj.errors.as_json())
    return JsonResponse(response.__dict__)

# 获取未审核用户列表（后台扫码创建用户）
@csrf_exempt
def get_audit_user(request):
    response = Response.ResponseObj()
    if request.method == "GET":
        company_id = request.GET.get('company_id')
        order = request.GET.get('order', '-create_date')
        forms_obj = UserSelectForm(request.GET)
        if forms_obj.is_valid():

            current_page = forms_obj.cleaned_data['current_page']
            length = forms_obj.cleaned_data['length']
            objs = models.zgld_temp_userprofile.objects.select_related('company').filter(company_id=company_id).order_by(order)
            count = objs.count()

            if length != 0:
                start_line = (current_page - 1) * length
                stop_line = start_line + length
                objs = objs[start_line: stop_line]

            ret_data = []
            department_objs = models.zgld_department.objects.filter(company_id=company_id).values('id', 'name')
            department_list_all = list(department_objs) if department_objs else []

            for obj in objs:
                departmane_list = obj.department
                if departmane_list:
                    departmane_list = json.loads(departmane_list)
                    if len(departmane_list) != 0:
                        departmane_list = [int(i) for i in departmane_list]
                    else:
                        departmane_list = []
                    department_name_list = []
                    for department_dict in department_list_all:
                        id = department_dict.get('id')
                        name = department_dict.get('name')
                        if int(id) in departmane_list:
                            department_name_list.append(name)
                    department = ', '.join(department_name_list)
                    ret_data.append({
                        'temp_user_id': obj.id,

                        'username': obj.username,
                        'create_date': obj.create_date,

                        'position': obj.position,
                        'wechat': obj.wechat,  # 代表注册企业微信注册时的电话
                        'mingpian_phone': obj.mingpian_phone,  # 名片显示的手机号
                        'wechat_phone': obj.wechat_phone,  # 代表注册企业微信注册时的电话

                        'company': obj.company.name,
                        'company_id': obj.company_id,
                        'department': department,
                        'department_id': departmane_list,

                    })
                    #  查询成功 返回200 状态码

            response.code = 200
            response.msg = '查询成功'
            response.data = {
                'ret_data': ret_data,
                'data_count': count,
                'department_list': department_list_all
            }
        else:
            response.code = 301
            response.msg = json.loads(forms_obj.errors.as_json())

    return JsonResponse(response.__dict__)

#  增删改 用户表
#  csrf  token验证
@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def user_oper(request, oper_type, o_id):
    response = Response.ResponseObj()

    if request.method == "POST":
        global userid
        # 添加用户
        if oper_type == "add":

            form_data = {
                'user_id': request.GET.get('user_id'),
                'username': request.POST.get('username'),
                'password': request.POST.get('password'),
                # 'role_id': request.POST.get('role_id'),
                'company_id': request.POST.get('company_id'),
                'position': request.POST.get('position'),
                'wechat_phone': request.POST.get('phone'), ##
                'mingpian_phone': request.POST.get('mingpian_phone')

            }

            #  创建 form验证 实例（参数默认转成字典）
            forms_obj = UserAddForm(form_data)

            if forms_obj.is_valid():
                print("验证通过")

                # user_id = request.GET.get('user_id')
                userid = str(int(time.time()*1000000))   # 成员UserID。对应管理端的帐号，企业内必须唯一
                username = forms_obj.cleaned_data.get('username')
                password = forms_obj.cleaned_data.get('password')
                # role_id = forms_obj.cleaned_data.get('role_id')
                company_id = forms_obj.cleaned_data.get('company_id')
                position = forms_obj.cleaned_data.get('position')
                wechat_phone = forms_obj.cleaned_data.get('wechat_phone')
                mingpian_phone = forms_obj.cleaned_data.get('mingpian_phone')


                available_user_num = models.zgld_company.objects.filter(id=company_id)[0].mingpian_available_num
                used_user_num  = models.zgld_userprofile.objects.filter(company_id=company_id).count() #


                print('----- 明片最大开通数 | 开通数------>>',available_user_num,used_user_num)
                if  int(used_user_num) >= int(available_user_num): # 开通的用户数量 等于 == 该公司最大可用名片数
                    response.code = 302
                    response.msg = "超过明片最大开通数,请您联系管理员"
                    return JsonResponse(response.__dict__)

                elif int(used_user_num) < int(available_user_num):  # 开通的用户数量 小于 < 该公司最大可用名片数,才能继续开通
                    depart_id_list = []
                    department_id = request.POST.get('department_id')
                    print('-----department_id---->',department_id)

                    rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)

                    if  department_id:
                        depart_id_list = json.loads(department_id)

                        objs = models.zgld_department.objects.filter(id__in=depart_id_list)
                        if objs:
                            for c_id in objs:
                                department_company_id = c_id.company_id

                                if str(department_company_id) != str(forms_obj.cleaned_data['company_id']):
                                    response.code = 404
                                    response.msg = '非法请求'
                                    return JsonResponse(response.__dict__)

                    token_ret = jianrong_create_qiyeweixin_access_token(company_id)
                    get_user_data = {
                        'access_token': token_ret
                    }

                    if len(depart_id_list) == 0:
                        depart_id_list = [1]

                    post_user_data = {
                        'userid' :  userid,
                        'name': username,
                        'position': position,
                        'mobile' :  wechat_phone,
                        'department': depart_id_list
                    }

                    add_user_url = Conf['add_user_url']
                    print('-------->>',json.dumps(post_user_data))

                    s = requests.session()
                    s.keep_alive = False  # 关闭多余连接
                    ret = s.post(add_user_url, params=get_user_data, data=json.dumps(post_user_data))

                    # ret = requests.post(add_user_url, params=get_user_data, data=json.dumps(post_user_data))

                    print('-----requests----->>', ret.text)

                    weixin_ret = json.loads(ret.text)
                    if  weixin_ret.get('errmsg') == 'created': # 在企业微信中创建用户成功
                        token = account.get_token(account.str_encrypt(password))

                        obj = models.zgld_userprofile.objects.create(
                            userid= userid,
                            username=username,
                            password=account.str_encrypt(password),
                            # role_id=role_id,
                            company_id=company_id,
                            position=position,
                            wechat_phone=wechat_phone,
                            mingpian_phone=mingpian_phone,
                            token=token
                        )
                        if depart_id_list[0] == 1:
                            depart_id_list = []
                        obj.department = depart_id_list

                        product_function_type = obj.company.product_function_type
                        if product_function_type != 3: # (3, '公众号版')
                            # 生成企业用户二维码
                            data_dict ={ 'user_id': obj.id, 'customer_id': ''}
                            tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))

                        _data = {
                            'company_id': company_id,
                            'userid': userid,
                        }
                        tasks.qiyeweixin_user_get_userinfo.delay(_data)

                        response.code = 200
                        response.msg = "添加用户成功"

                    else:

                        response.code = weixin_ret['errcode']
                        response.msg = "企业微信返回错误,%s" % weixin_ret['errmsg']


            else:
                    print("验证不通过")
                    print(forms_obj.errors)
                    response.code = 301
                    print(forms_obj.errors.as_json())
                    response.msg = json.loads(forms_obj.errors.as_json())

        # 删除用户
        elif oper_type == "delete":
            # 删除 ID
            _type = request.GET.get('type')

            if _type == 'temp_user':
                user_objs = models.zgld_temp_userprofile.objects.filter(id=o_id)
                if user_objs:
                    user_objs.delete()
                    response.code = 200
                    response.msg = "删除成功"
                else:
                    response.code = 302
                    response.msg = '用户ID不存在'

            else:

                    user_objs = models.zgld_userprofile.objects.filter(id=o_id)
                    if user_objs:
                        company_id =  user_objs[0].company_id

                        token_ret = jianrong_create_qiyeweixin_access_token(company_id)
                        get_user_data = {
                            'access_token': token_ret
                        }

                        userid = user_objs[0].userid
                        if userid:
                            get_user_data['userid'] = userid

                            s = requests.session()
                            s.keep_alive = False  # 关闭多余连接
                            ret = s.get(Conf['delete_user_url'], params=get_user_data)

                            # ret = requests.get(Conf['delete_user_url'], params=get_user_data)

                            weixin_ret = json.loads(ret.text)
                            print('微信删除 weixin_ret 接口返回-------->>',weixin_ret)

                            if weixin_ret['errcode'] == 0:
                                user_objs.delete()
                                print('删除成功------->>')
                                response.code = 200
                                response.msg = "删除成功"

                            elif weixin_ret['errcode'] == 60111: # userId not found
                                user_objs.delete()
                                print('userId not found并删除本地用户------->>')
                                response.code = 200
                                response.msg = "删除成功"

                            else:
                                print('------ "企业微信返回错误,%s" % weixin_ret ---->',"企业微信返回错误,%s" , weixin_ret['errmsg'])
                                response.code = weixin_ret['errcode']
                                response.msg = "企业微信返回错误,%s" % weixin_ret['errmsg']

                        else:
                            response.code = '302'
                            response.msg = "userid不存在"
                    else:
                        response.code = 302
                        response.msg = '用户ID不存在'

        # 修改用户
        elif oper_type == "update":

            print('-------->>',request.POST)
            _type = request.GET.get('type')

            user_id =  request.GET.get('user_id')
            wechat =  request.POST.get('wechat')
            wechat_phone = request.POST.get('phone')
            if request.POST.get('wechat_phone'):
                wechat_phone = request.POST.get('wechat_phone')
            mingpian_phone =  request.POST.get('mingpian_phone')
            department_id = request.POST.get('department_id')
            if department_id:
                department_id = json.loads(department_id)
            company_id = request.POST.get('company_id')
            # 获取ID 用户名 及 角色
            form_data = {
                'o_id': o_id,
                'user_id': request.GET.get('user_id'),
                'username': request.POST.get('username'),
                'company_id': request.POST.get('company_id'),
                'position': request.POST.get('position'),

                'wechat_phone': wechat_phone,
                'mingpian_phone': mingpian_phone,

            }

            forms_obj = UserUpdateForm(form_data)

            if forms_obj.is_valid():
                print("验证通过")

                print(forms_obj.cleaned_data)
                username = forms_obj.cleaned_data.get('username')
                # role_id = forms_obj.cleaned_data.get('role_id')
                position = forms_obj.cleaned_data.get('position')

                wechat_phone =   forms_obj.cleaned_data.get('wechat_phone')
                mingpian_phone = forms_obj.cleaned_data.get('mingpian_phone')

                if _type == 'temp_user':

                    temp_userprofile_objs = models.zgld_temp_userprofile.objects.filter(id=o_id)
                    if temp_userprofile_objs:
                        temp_userprofile_objs.update(
                            username=username,
                            position=position,
                            wechat=wechat,
                            wechat_phone=wechat_phone,
                            mingpian_phone=mingpian_phone,
                        )

                    print('-- department_id --->',department_id)
                    user_obj = temp_userprofile_objs[0]
                    user_obj.department = department_id
                    user_obj.save()
                    response.code = 200
                    response.msg = "修改成功"


                else:

                    user_objs = models.zgld_userprofile.objects.select_related('company').filter(id=o_id)

                    if user_objs:
                        userid = user_objs[0].userid
                        token_ret = jianrong_create_qiyeweixin_access_token(company_id)
                        get_user_data = {
                            'access_token': token_ret
                        }

                        if len(department_id) == 0:
                            department_id = [1]
                        post_user_data = {}
                        post_user_data['userid'] = userid
                        post_user_data['name'] = username
                        post_user_data['position'] = position
                        post_user_data['department'] = department_id
                        post_user_data['mobile'] = wechat_phone
                        # print('------- 请求发送的数据 ----->>' ,get_user_data, department_id ,"\n" ,post_user_data,json.dumps(post_user_data))

                        s = requests.session()
                        s.keep_alive = False  # 关闭多余连接
                        ret = s.post(Conf['update_user_url'], params=get_user_data, data=json.dumps(post_user_data))


                        # ret = requests.post(Conf['update_user_url'], params=get_user_data, data=json.dumps(post_user_data))

                        weixin_ret = ret.json()

                        print('------- 请求返回的数据----->>', weixin_ret)

                        if department_id[0] == 1 and len(department_id) == 1:
                            department_id = []


                        errcode = weixin_ret.get('errcode')
                        errmsg =weixin_ret.get('errmsg')

                        if weixin_ret['errmsg'] == 'updated':
                            # print('----wechat_phone--->>',wechat_phone,mingpian_phone)
                            user_objs.update(
                                username=username,
                                # role_id=role_id,
                                # company_id=company_id,
                                position=position,
                                wechat_phone=wechat_phone,
                                mingpian_phone=mingpian_phone
                            )

                            _data = {
                                'company_id': company_id,
                                'userid': userid,
                            }
                            tasks.qiyeweixin_user_get_userinfo.delay(_data) # 获取用户头像


                            user_obj = user_objs[0]
                            user_obj.department = department_id
                            user_obj.save()
                            response.code = 200
                            response.msg = "修改成功"

                            # 生成海报
                            # data_dict = {'user_id': user_id, 'customer_id': ''}
                            # tasks.create_user_or_customer_small_program_poster.delay(json.dumps(data_dict))

                        else:
                            response.code = errcode
                            response.msg = errmsg

                    else:
                        response.code = 303
                        response.msg = json.loads(forms_obj.errors.as_json())

            else:
                print("验证不通过")
                print(forms_obj.errors)
                response.code = 301
                print(forms_obj.errors.as_json())
                #  字符串转换 json 字符串
                response.msg = json.loads(forms_obj.errors.as_json())

        # 修改用户启用状态
        elif oper_type == "update_status":

            status = request.POST.get('status')    #(1, "启用"),  (2, "未启用"),
            boss_status = request.POST.get('boss_status')    #(1, "启用"),  (2, "未启用"),
            article_admin_status = request.POST.get('article_admin_status')    #(1, "启用"),  (2, "未启用"),
            user_id = request.GET.get('user_id')

            objs = models.zgld_userprofile.objects.filter(id=o_id)

            if objs:

                if int(user_id) == int(o_id):
                    response.code = 305
                    response.msg = "不能修改自己"

                elif status:
                    objs.update(status=status)
                    response.code = 200
                    response.msg = "修改成功"

                elif boss_status:
                    objs.update(boss_status=boss_status)
                    response.code = 200
                    response.msg = "修改成功"

                elif article_admin_status:
                    objs.update(article_admin_status=article_admin_status)
                    response.code = 200
                    response.msg = "修改成功"

        # 生成企业用户二维码
        elif oper_type == 'create_small_program_qr_code':
            user_id = request.POST.get('user_id')
            user_obj = models.zgld_userprofile.objects.filter(id=user_id)
            if user_obj:


                # tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))

                data_dict = {
                    'user_id': user_id,
                    'customer_id': ''
                }

                url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/create_user_or_customer_qr_code'

                print('--------mycelery 使用 request post_的数据 ------->>',data_dict)

                s = requests.session()
                s.keep_alive = False  # 关闭多余连接
                response_ret = s.post(url , data=data_dict)

                # response_ret = requests.post(url , data=data_dict)
                response_ret = response_ret.json()

                print('-------- mycelery/触发 celery  返回的结果 -------->>',response_ret)

                qr_code =  response_ret['data'].get('qr_code')
                response.data = {
                    'qr_code': qr_code
                }
                response.code = 200
                response.msg = "生成用户二维码成功"

            else:
                response.code = 301
                response.msg = "用户不存在"

        # 获取部门列表 接口返回
        elif oper_type == 'sync_user_tongxunlu':
            company_id = o_id

            token_ret = jianrong_create_qiyeweixin_access_token(company_id)
            get_user_data = {
                'access_token': token_ret
            }

            department_list_url =  'https://qyapi.weixin.qq.com/cgi-bin/department/list'

            s = requests.session()
            s.keep_alive = False  # 关闭多余连接
            department_list_ret = s.get(department_list_url, params=get_user_data)

            # department_list_ret = requests.get(department_list_url, params=get_user_data)

            department_list_ret = department_list_ret.json()
            department_list = department_list_ret.get('department')
            print('-------- 获取部门列表 接口返回----------->>',json.dumps(department_list_ret))

            if department_list:
                for dep_dict in department_list:
                    department_id = dep_dict.get('id')

                    department_liebiao = dep_dict.get('department') # 已经存在的部门列表

                    user_simplelist_url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist'
                    get_user_data['department_id'] = department_id

                    s = requests.session()
                    s.keep_alive = False  # 关闭多余连接
                    user_simplelist_ret = s.get(user_simplelist_url, params=get_user_data)

                    # user_simplelist_ret = requests.get(user_simplelist_url, params=get_user_data)

                    print('----- 获取部门成员 返回接口信息----->>', json.dumps(user_simplelist_ret.json()))
                    user_simplelist_ret = user_simplelist_ret.json()
                    errcode = user_simplelist_ret.get('errcode')
                    errmsg = user_simplelist_ret.get('errmsg')
                    userlist = user_simplelist_ret.get('userlist')

                    if userlist:
                        print('------- 获取-客户信息【成功】 ------->>',user_simplelist_ret)

                        for user_dict in userlist:
                            username = user_dict.get('name')
                            userid = user_dict.get('userid')
                            department_list = user_dict.get('department')
                            password = '123456'
                            token = account.get_token(account.str_encrypt(password))
                            objs =  models.zgld_userprofile.objects.filter(userid=userid,company_id=company_id)

                            if objs:
                                user_id = objs[0].id
                                print('-------- 用户数据成功已存在 username | userid | user_id -------->>',username,userid,user_id)
                            else:
                                obj = models.zgld_userprofile.objects.create(
                                    userid=userid,
                                    username= username,
                                    password= account.str_encrypt(password),
                                    # role_id=role_id,
                                    company_id=company_id,
                                    # position='',
                                    # wechat_phone='',
                                    # mingpian_phone= '',
                                    token=token
                                )

                                _data = {
                                    'company_id': company_id,
                                    'userid': userid,
                                }
                                tasks.qiyeweixin_user_get_userinfo.delay(_data) # 获取头像信息

                                print('-------- 同步用户数据成功 user_id：-------->>',obj.id)

                                # if department_list:
                                #     obj.department = department_list

                                # 生成企业用户二维码
                                product_function_type = obj.company.product_function_type
                                if product_function_type != 3:  # (3, '公众号版')

                                    data_dict = {'user_id': obj.id, 'customer_id': ''}
                                    tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))

                        response.code = 200
                        response.msg = "同步成功并生成用户二维码成功"

                    else:
                        print('---- 获取部门成员 [报错]：------>',errcode,"|",errmsg)

        # 用户添加自己的信息入临时库
        elif oper_type == 'scan_code_to_add_user':
            user_id = request.GET.get('user_id')

            userprofile_obj = models.zgld_admin_userprofile.objects.get(id=user_id)
            company_id = userprofile_obj.company_id

            form_data = {
                'user_id': user_id,
                'company_id': company_id,
                'username': request.POST.get('username'),
                'position': request.POST.get('position'),
                'wechat': request.POST.get('wechat'),
                'wechat_phone': request.POST.get('wechat_phone'),       ## 微信绑定的手机号
                'mingpian_phone': request.POST.get('mingpian_phone')    # 名片显示的手机号

            }

            #  创建 form验证 实例（参数默认转成字典）
            forms_obj = ScanCodeToAddUserForm(form_data)

            if forms_obj.is_valid():
                print("验证通过")

                depart_id_list = []
                department_id = request.POST.get('department_id')
                print('-----department_id---->', department_id)



                if department_id:
                    depart_id_list = json.loads(department_id)

                username = forms_obj.cleaned_data.get('username')
                position = forms_obj.cleaned_data.get('position')
                wechat_phone = forms_obj.cleaned_data.get('wechat_phone')
                mingpian_phone = forms_obj.cleaned_data.get('mingpian_phone')
                wechat = request.POST.get('wechat')


                obj = models.zgld_temp_userprofile.objects.create(

                    username=username,
                    company_id=company_id,
                    position=position,
                    wechat_phone=wechat_phone,
                    mingpian_phone=mingpian_phone,
                    wechat=wechat,

                )

                obj.department = json.dumps(depart_id_list)
                obj.save()

                if int(company_id) in [1, 2]: # 当给医美雷达公司添加的时候，才给提示

                    ### 提醒董庆豪和尚露 审核用户
                    corpid = 'wx81159f52aff62388'  # 企业ID
                    corpsecret = 'dGWYuaTTLi6ojhPYG1_mqp9GCMTyLkl2uwmsNkjsSjw'  # 应用的凭证密钥
                    redis_access_token_name = "access_token_send_msg"  # 存放在redis中的access_token对应key的名称
                    _obj = WorkWeixinOper(corpid, corpsecret, redis_access_token_name)

                    url = 'http://api.zhugeyingxiao.com/zhugeleida/public/myself_tools/approval_audit?company_id={company_id}'.format(
                        company_id=company_id
                    )
                    msg = """【审核用户】：{username}\n【点击链接】：{url}\n """.format(
                        username=username,
                        url=url,
                    )
                                                    # 尚露↓
                    openid_list = [1531186501974, 1531464629357, 1531476018476]
                    for i in openid_list:
                        _obj.send_message(
                            agentid=1000005,
                            msg=msg,
                            touser=i
                        )

                response.code = 200
                response.msg = "添加用户成功"





            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 管理员审核用户【批量】入库
        elif oper_type == 'approval_storage_user_info':
            print('---- 审核de 批量 ----->>')
            user_id_list = request.POST.get('user_id_list')
            _type = request.GET.get('type')

            print('---- 审核de user_id_list 1  ----->>', user_id_list)

            if user_id_list:
                user_id_list = json.loads(user_id_list)
                print('---- 审核de user_id_list 2 ----->>', user_id_list)

                # response.code = 200
                # response.msg = "审核用户成功"
                # return JsonResponse(response.__dict__)

                temp_userprofile_objs =models.zgld_temp_userprofile.objects.filter(id__in=user_id_list)
                if temp_userprofile_objs:

                    for temp_obj in temp_userprofile_objs:
                        company_id = temp_obj.company_id

                        department_id_list = json.loads(temp_obj.department)

                        if len(department_id_list) == 0:
                            department_id_list = [1]


                        print("验证通过")
                        userid = str(int(time.time() * 1000))   # 成员UserID。对应管理端的帐号，企业内必须唯一
                        password = '123456'

                        available_user_num = models.zgld_company.objects.filter(id=company_id)[0].mingpian_available_num
                        used_user_num = models.zgld_userprofile.objects.filter(company_id=company_id).count()  #

                        print('-----明片最大开通数 | 已开通数------>>', available_user_num, used_user_num)
                        if int(used_user_num) >= int(available_user_num):  # 开通的用户数量 等于 == 该公司最大可用名片数
                            response.code = 302
                            response.msg = "超过明片最大开通数,请您联系管理员"
                            return JsonResponse(response.__dict__)

                        elif int(used_user_num) < int(available_user_num):  # 开通的用户数量 小于 < 该公司最大可用名片数,才能继续开通

                            token = account.get_token(account.str_encrypt(password))

                            username = temp_obj.username
                            position = temp_obj.position
                            wechat= temp_obj.wechat
                            wechat_phone= temp_obj.wechat_phone
                            mingpian_phone= temp_obj.mingpian_phone

                            temp_user_info_dict = {
                                'userid': userid,
                                'password': account.str_encrypt(password),
                                'token': token,
                                'username': username,
                                'company_id':company_id,
                                'position': position,
                                'wechat':  wechat,
                                'wechat_phone': wechat_phone,
                                'mingpian_phone': mingpian_phone,

                            }

                            token_ret = jianrong_create_qiyeweixin_access_token(company_id)
                            get_user_data = {
                                'access_token': token_ret
                            }

                            post_user_data = {}
                            post_user_data['userid'] = userid
                            post_user_data['name'] = username
                            post_user_data['position'] = position
                            post_user_data['mobile'] = wechat_phone
                            post_user_data['department'] = department_id_list
                            add_user_url = Conf['add_user_url']
                            key_name = "company_%s_tongxunlu_token" % (company_id)
                            print('-------->>', json.dumps(post_user_data))

                            s = requests.session()
                            s.keep_alive = False  # 关闭多余连接
                            ret = s.post(add_user_url, params=get_user_data, data=json.dumps(post_user_data))

                            # ret = requests.post(add_user_url, params=get_user_data, data=json.dumps(post_user_data))


                            print('-----requests----->>', ret.text)

                            weixin_ret = json.loads(ret.text)
                            if weixin_ret.get('errmsg') == 'created':  # 在企业微信中创建用户成功

                                obj = models.zgld_userprofile.objects.create(**temp_user_info_dict)
                                if len(department_id_list) == 1  and department_id_list[0] == 1:
                                    department_id_list = []

                                obj.department = department_id_list
                                if _type == 'phone_audit':
                                    obj.status = 1

                                obj.save()
                                models.zgld_temp_userprofile.objects.filter(id=temp_obj.id).delete() # 删除已经通过审核的员工。

                                product_function_type = obj.company.product_function_type
                                if product_function_type != 3:  # (3, '公众号版')
                                    # 生成企业用户二维码
                                    data_dict = {'user_id': obj.id, 'customer_id': ''}
                                    tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))

                                # 获取用户头像信息
                                _data = {
                                    'company_id': company_id,
                                    'userid': userid,
                                }
                                tasks.qiyeweixin_user_get_userinfo.delay(_data)

                                response.code = 200
                                response.msg = "添加用户成功"

                            else:
                                rc = redis.StrictRedis(host='redis_host', port=6379, db=8, decode_responses=True)
                                rc.delete(key_name)
                                response.code = weixin_ret['errcode']
                                response.msg = "企业微信返回错误,%s" % weixin_ret['errmsg']


                else:
                    response.code = 301
                    response.msg =  '用户临时表无数据'


    else :
        # 生成 扫描的用户二维码
        if  oper_type == "create_scan_code":
            user_id = request.GET.get('user_id')
            from zhugeleida.public.common import create_scan_code_userinfo_qrcode
            obj = models.zgld_admin_userprofile.objects.get(id=user_id)

            token = obj.token
            timestamp = str(int(time.time() * 1000))

            rand_str = account.str_encrypt(timestamp + token)
            timestamp = timestamp

            three_service_objs = models.zgld_three_service_setting.objects.filter(three_services_type=1)  # 公众号
            qywx_config_dict = ''
            if three_service_objs:
                three_service_obj = three_service_objs[0]
                qywx_config_dict = three_service_obj.config
                if qywx_config_dict:
                    qywx_config_dict = json.loads(qywx_config_dict)

            leida_http_url = qywx_config_dict.get('domain_urls').get('leida_http_url')


            url = '%s/#/gongzhonghao/zhuceyonghu?rand_str=%s&timestamp=%s&user_id=%d' % (
                leida_http_url,rand_str, timestamp, int(user_id))
            data = {
                'url': url,
                'admin_uid': user_id

            }
            response_ret  = create_scan_code_userinfo_qrcode(data)

            qrcode_url = response_ret.data.get('qrcode_url')
            if qrcode_url:
                response = response_ret
                response.code = 200
                response.msg = "添加成功"
                print('---- create_code_to_add_user url -->', url)



            else:
                response.code = 302
                response.msg = "用户不存在"

        else:
            response.code = 402
            response.msg = "请求异常"

    return JsonResponse(response.__dict__)


