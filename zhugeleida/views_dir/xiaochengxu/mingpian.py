from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import time
import datetime
from publicFunc.condition_com import conditionCom
from zhugeleida.public.common import action_record

from zhugeleida.forms.xiaochengxu.user_verify import UserAddForm, UserUpdateForm, UserSelectForm,UserAllForm
import json,os,sys
from django.db.models import Q
from django.db.models import F
import requests
from zhugeapi_celery_project import tasks

# 展示单个的名片信息
@csrf_exempt
@account.is_token(models.zgld_customer)
def mingpian(request):
    response = Response.ResponseObj()
    if request.method == "GET":  # 获取单个名片的信息
        forms_obj = UserSelectForm(request.GET)
        if forms_obj.is_valid():
            user_id = request.GET.get('uid')  # 用户 id
            customer_id = request.GET.get('user_id')
            # current_page = forms_obj.cleaned_data['current_page']
            # length = forms_obj.cleaned_data['length']

            order = request.GET.get('order', '-create_date')
            field_dict = {
                'id': '',
                'username': '__contains',
                'role__name': '__contains',
                'company__name': '__contains',
            }

            q = conditionCom(request, field_dict)
            q.add(Q(**{'id': user_id}), Q.AND)

            global remark
            accesslog_obj = models.zgld_accesslog.objects.filter(user_id=user_id,customer_id=customer_id,action=1)

            action_count = accesslog_obj.count()
            if action_count == 0:
                remark = '首次查看您的名片,沟通从此刻开始'
            elif action_count == 1:
                remark = '查看您的名片第%s次,把握深度交流的机会' % (action_count)
            elif action_count == 2:
                remark = '查看您的名片第%s次,建议标注重点客户' % (action_count)
            elif action_count > 3:
                remark = '查看您的名片第%s次,成交在望' % (action_count)

            customer_obj = models.zgld_customer.objects.filter(id=customer_id)
            if customer_obj:
                customer_username = customer_obj[0].username
                if customer_username: # 只有客户名字存在时候，才去记录日志并通知用户。
                    data = request.GET.copy()
                    data['action'] = 1
                    action_record(data, remark)  # 记录访问动作

            models.zgld_userprofile.objects.select_related('company').filter(id=user_id).update(popularity=F('popularity') + 1)  # 查看的个数加1
            objs = models.zgld_userprofile.objects.select_related('company').filter(q).order_by(order)
            count = objs.count()


            ret_data = {}
            is_praise = False
            is_sign = False

            if objs:
                for obj in objs:
                    up_down_obj = models.zgld_up_down.objects.select_related('user', 'customer').filter(user_id=user_id,customer_id=customer_id)
                    if up_down_obj:
                        is_praise = up_down_obj[0].up

                    up_down_sign_obj = models.zgld_up_down_sign.objects.filter(user_id=obj.id, customer_id=customer_id)
                    if up_down_sign_obj:
                        is_sign = up_down_sign_obj[0].up

                    # photo_data = models.zgld_user_photo.objects.filter(user_id=user_id,photo_type=1).values('id', 'photo_url').order_by(
                    #     '-create_date')
                    tag_data = models.zgld_userprofile.objects.get(id=user_id).zgld_user_tag_set.values('id',
                                                                                                        'name').order_by(
                        '-create_date')

                    objs = models.zgld_userprofile.objects.filter(id=user_id)
                    sign_num = objs[0].sign_num
                    # chatinfo_count = models.zgld_chatinfo.objects.filter(userprofile_id=user_id,customer_id=customer_id,send_type=1,is_customer_new_msg=True).count()
                    mingpian_avatar_obj = models.zgld_user_photo.objects.filter(user_id=user_id,photo_type=2).order_by('-create_date')

                    mingpian_avatar = ''
                    if mingpian_avatar_obj:
                        mingpian_avatar =  mingpian_avatar_obj[0].photo_url
                    else:
                        mingpian_avatar =  obj.avatar
                    mingpian_phone  = obj.mingpian_phone  if   obj.mingpian_phone else  obj.wechat_phone

                    memo_name = obj.memo_name
                    if memo_name:
                        username = memo_name
                    else:
                        username = obj.username

                    ret_data = {
                        'id': obj.id,
                        'username': username,
                        'avatar': obj.avatar,
                        'company': obj.company.name,
                        'address': obj.company.address,
                        'position': obj.position,
                        'email': obj.email,
                        'wechat': obj.wechat,  # 微信号
                        'mingpian_avatar': mingpian_avatar,  #名片的头像
                        'mingpian_phone':  mingpian_phone if obj.is_show_phone else '',  # 名片手机号
                        'create_date': obj.create_date,  # 创建时间
                        'popularity_num': obj.popularity,  # 被查看多少次。
                        'praise_num': obj.praise,  # 点赞多少次
                        'forward_num': obj.forward,  # 转发多少次
                        'is_praise': is_praise,
                        'sign': obj.sign,  # 签名
                        'is_sign': is_sign,  # 签名
                        'sign_num': sign_num,
                        'photo': '', #预留照片墙
                        'tag': list(tag_data),

                    }

                # 查询成功 返回200 状态码
                response.code = 200
                response.msg = '查询成功'
                response.data = {
                    'ret_data': ret_data,
                    'data_count': count,
                }


        else:
            response.code = 402
            response.msg = "请求异常"
            response.data = json.loads(forms_obj.errors.as_json())

    return JsonResponse(response.__dict__)


# 展示全部的名片、记录各种动作到日志中
@csrf_exempt
# @account.is_token(models.zgld_customer)
def mingpian_oper(request, oper_type):
    response = Response.ResponseObj()

    if request.method == "GET":

        forms_obj = UserSelectForm(request.GET)
        if forms_obj.is_valid():
            # 记录拨打手机
            if oper_type == 'calling':
                remark = '拨打您的手机'
                data = request.GET.copy()
                data['action'] = 10
                action_record(data, remark)
                response.code = 200
                response.msg = '记录成功'


            elif oper_type == 'save_phone': # 弃用 小程序 没有拨打手机号。
                remark = '保存了您的电话,可以考虑拜访'
                data = request.GET.copy()
                data['action'] = 8
                action_record(data, remark)
                response.code = 200
                response.msg = '记录成功'

            elif oper_type == 'save_wechat':
                remark = '复制了您的微信,留意微信新朋友消息'
                data = request.GET.copy()
                data['action'] = 5
                action_record(data, remark)
                response.code = 200
                response.msg = '记录成功'


            elif oper_type == 'praise':  # 点赞功能，觉得你靠谱
                user_id = request.GET.get('uid')  # 用户 id
                customer_id = request.GET.get('user_id')  # 客户 id

                updown_obj = models.zgld_up_down.objects.filter(
                    user_id=user_id,  # 被赞的用户
                    customer_id=customer_id,  # 赞或踩的客户
                )

                if not updown_obj:
                    models.zgld_up_down.objects.create(
                        user_id=user_id,  # 被赞的用户
                        customer_id=customer_id,  # 赞或踩的客户
                        up=True
                    )
                    remark = '觉得您非常靠谱'
                    data = request.GET.copy()
                    data['action'] = 9
                    action_record(data, remark)
                    objs = models.zgld_userprofile.objects.filter(id=user_id)
                    objs.update(praise=F('praise') + 1)
                    praise_num = objs[0].praise
                    is_praise = ''
                    up_down_obj = models.zgld_up_down.objects.filter(user_id=user_id, customer_id=customer_id)
                    if up_down_obj:
                        is_praise = up_down_obj[0].up
                    response.code = 200
                    response.data = {
                        'ret_data':
                            {
                                'praise_num': praise_num,
                                'is_praise': True,
                            }
                    }

                else:
                    praise_status = updown_obj[0].up
                    if praise_status == True:
                        remark = '取消了给你的靠谱评价'
                        updown_obj.update(up=False)
                        data = request.GET.copy()
                        data['action'] = 9
                        action_record(data, remark)
                        objs = models.zgld_userprofile.objects.filter(id=user_id)
                        objs.update(praise=F('praise') - 1)
                        praise_num = objs[0].praise

                        response.data = {
                            'ret_data':
                                {
                                    'praise_num': praise_num,
                                    'is_praise': False,
                                }
                        }
                        response.code = 200

                    elif praise_status == False:
                        remark = '觉得您非常靠谱'
                        updown_obj.update(up=True)
                        data = request.GET.copy()
                        data['action'] = 9
                        action_record(data, remark)
                        objs = models.zgld_userprofile.objects.filter(id=user_id)
                        objs.update(praise=F('praise') + 1)
                        praise_num = objs[0].praise

                        response.data = {
                            'ret_data':
                                {
                                    'praise_num': praise_num,
                                    'is_praise': True,
                                }
                        }
                        response.code = 200

                    print('----response.data----->',response.data)

            elif oper_type == 'forward':
                user_id = request.GET.get('uid')  # 用户 id

                remark = '转发了你的名片,你的人脉圈正在裂变'
                data = request.GET.copy()
                data['action'] = 6
                action_record(data, remark)
                models.zgld_userprofile.objects.filter(id=user_id).update(forward=F('forward') + 1)

            elif oper_type == 'up_sign':
                user_id = request.GET.get('uid')  # 用户 id
                customer_id = request.GET.get('user_id')  # 客户 id

                updown_obj = models.zgld_up_down_sign.objects.filter(
                    user_id=user_id,  # 被赞的用户
                    customer_id=customer_id,  # 赞或踩的客户
                )

                if not updown_obj:  # 表示签名没有被赞。
                    models.zgld_up_down_sign.objects.create(
                        user_id=user_id,  # 被赞的用户
                        customer_id=customer_id,  # 赞或踩的客户
                        up=True
                    )
                    remark = '赞了你的个性签名'
                    data = request.GET.copy()
                    data['action'] = 9
                    action_record(data, remark)
                    objs = models.zgld_userprofile.objects.filter(id=user_id)
                    objs.update(sign_num=F('sign_num') + 1)

                    sign_num = objs[0].sign_num
                    is_sign = False
                    up_down_obj = models.zgld_up_down_sign.objects.filter(user_id=user_id, customer_id=customer_id)
                    if up_down_obj:
                        is_sign = up_down_obj[0].up

                    response.data = {
                        'ret_data':
                            {
                                'sign_num': sign_num,
                                'is_sign': is_sign,
                            }
                    }


                else:
                    is_sign = False
                    objs = models.zgld_userprofile.objects.filter(id=user_id)
                    sign_num = objs[0].sign_num
                    up_down_obj = models.zgld_up_down_sign.objects.filter(user_id=user_id, customer_id=customer_id)
                    if up_down_obj:
                        is_sign = up_down_obj[0].up

                    response.data = {
                        'ret_data':
                            {
                                'sign_num': sign_num,
                                'is_sign': is_sign,
                            }
                    }

                    response.code = 200
                    response.msg = '已经点过赞'

            # 前端先用于生成海报的页面。用了用户体验度更高。
            elif oper_type == 'create_poster':

                customer_id = request.GET.get('user_id')
                user_id = request.GET.get('uid')  # 用户 id

                obj = models.zgld_userprofile.objects.get(id=user_id)

                mingpian_avatar_obj = models.zgld_user_photo.objects.filter(user_id=user_id, photo_type=2).order_by('-create_date')
                mingpian_avatar = ''
                if mingpian_avatar_obj:
                    mingpian_avatar =   mingpian_avatar_obj[0].photo_url
                else:
                    mingpian_avatar =  obj.avatar

                qr_obj = models.zgld_user_customer_belonger.objects.filter(user_id=user_id,customer_id=customer_id)
                qr_code = ''
                if qr_obj:
                    qr_code =  qr_obj[0].qr_code
                    print('----- customer_belonger poster 页面二维码 ------>>',qr_code)

                    poster_url = qr_obj[0].poster_url
                    if not  poster_url:
                        data_dict = {'user_id': user_id, 'customer_id': customer_id}
                        tasks.create_user_or_customer_small_program_poster.delay(json.dumps(data_dict))


                    if not  qr_code: # 如果为空的话,则使用雷达用户的二维码
                        qr_code =  obj.qr_code


                ret_data = {
                    'user_id': obj.id,
                    'user_avatar': mingpian_avatar,
                    'username': obj.username,
                    'position': obj.position,
                    'mingpian_phone': obj.mingpian_phone,
                    'company': obj.company.name,
                    'qr_code_url':   qr_code,
                }
                response.data = ret_data
                response.msg = "请求成功"
                response.code = 200

                # return render(request, 'create_poster.html',locals())

            # 保存名片海报
            elif oper_type == 'save_poster':

                remark = '保存了您的名片海报'
                data = request.GET.copy() # request.GET是不可变类型  copy一份
                data['action'] = 1
                action_record(data, remark)

                customer_id = request.GET.get('user_id')
                user_id = request.GET.get('uid')

                qr_obj = models.zgld_user_customer_belonger.objects.filter(user_id=user_id, customer_id=customer_id)
                poster_url = qr_obj[0].poster_url
                # if not poster_url:

                ret_data = {
                        'uid': user_id,
                        'poster_url': poster_url,
                    }
                print('-----save_poster ret_data --->>',ret_data)
                data_dict = {'user_id': user_id, 'customer_id': customer_id}
                tasks.create_user_or_customer_small_program_poster.delay(json.dumps(data_dict))
                print("------ celery 去生成海报 ---->", data_dict)

                response.data = ret_data
                response.msg = "请求成功"
                response.code = 200



                # BASE_DIR = os.path.join(settings.BASE_DIR, 'statics','zhugeleida','imgs','xiaochengxu','user_poster',)
                # print('---->',BASE_DIR)
                #
                #
                # # option = webdriver.ChromeOptions()
                # # mobileEmulation = {'deviceName': 'iPhone 6'}
                # # option.add_experimental_option('mobileEmulation', mobileEmulation)
                # # driver = webdriver.Chrome(BASE_DIR +'./chromedriver_2.36.exe',chrome_options=option)
                #
                # platform = sys.platform     # 获取平台
                # phantomjs_path = os.path.join(settings.BASE_DIR, 'zhugeleida', 'views_dir', 'tools')
                #
                #
                # if 'linux' in platform:
                #     phantomjs_path = phantomjs_path   + '/phantomjs'
                #
                # else:
                #     phantomjs_path =  phantomjs_path  + '/phantomjs.exe'
                # print('----- phantomjs_path ----->>',phantomjs_path)
                #
                # driver = webdriver.PhantomJS(phantomjs_path)
                # driver.implicitly_wait(10)
                #
                # rand_str = request.GET.get('rand_str')
                # timestamp = request.GET.get('timestamp')
                # customer_id = request.GET.get('user_id')
                # user_id = request.GET.get('uid')
                #
                # url = 'http://api.zhugeyingxiao.com/zhugeleida/xiaochengxu/mingpian/poster_html?rand_str=%s&timestamp=%s&user_id=%d&uid=%d' % (rand_str,timestamp,int(customer_id),int(user_id))
                #
                # print('----save_poster-->',url)
                #
                # try:
                #     driver.get(url)
                #     now_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                #     user_poster_file_temp = '/%s_%s_poster_temp.png' % (customer_id,user_id)
                #     user_poster_file = '/%s_%s_%s_poster.png' % (customer_id,user_id,now_time)
                #
                #     driver.save_screenshot(BASE_DIR  + user_poster_file_temp)
                #     driver.get_screenshot_as_file(BASE_DIR + user_poster_file_temp)
                #
                #     element = driver.find_element_by_id("jietu")
                #     print(element.location)  # 打印元素坐标
                #     print(element.size)      # 打印元素大小
                #
                #     left = element.location['x']
                #     top = element.location['y']
                #     right = element.location['x'] + element.size['width']
                #     bottom = element.location['y'] + element.size['height']
                #
                #     im = Image.open( BASE_DIR  + user_poster_file_temp)
                #     im = im.crop((left, top, right, bottom))
                #
                #
                #     print (len(im.split()))  # test
                #     if len(im.split()) == 4:
                #         # prevent IOError: cannot write mode RGBA as BMP
                #         r, g, b, a = im.split()
                #         im = Image.merge("RGB", (r, g, b))
                #         im.save( BASE_DIR  + user_poster_file)
                #     else:
                #         im.save( BASE_DIR  + user_poster_file)
                #
                #     poster_url = 'statics/zhugeleida/imgs/xiaochengxu/user_poster%s' % user_poster_file
                #     if os.path.exists(BASE_DIR  + user_poster_file_temp): os.remove(BASE_DIR  + user_poster_file_temp)
                #     print('---------生成海报URL-------->', poster_url)
                #
                #     ret_data = {
                #         'user_id': user_id,
                #         'poster_url': poster_url,
                #     }
                #     print('-----save_poster ret_data --->>',ret_data)
                #     response.data = ret_data
                #     response.msg = "请求成功"
                #     response.code = 200
                #
                # except Exception as e:
                #     response.msg = "PhantomJS截图失败"
                #     response.code = 400
                #     driver.quit()



        else:
            response.code = 402
            response.msg = "请求异常"
            response.data = json.loads(forms_obj.errors.as_json())

        if oper_type == "all":  # 获取所有的名片
            print('---request.GET-->>', request.GET)
            forms_obj = UserAllForm(request.GET)
            if forms_obj.is_valid():
                user_id = request.GET.get('uid')  # 用户 id
                customer_id = request.GET.get('user_id')  # 客户 id
                # current_page = forms_obj.cleaned_data['current_page']
                # length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-create_date')

                field_dict = {
                    'id': '',
                }
                q = conditionCom(request, field_dict)
                q.add(Q(**{'customer_id': customer_id}), Q.AND)

                objs = models.zgld_user_customer_belonger.objects.select_related('user', 'customer').filter(q).order_by(order)
                count = objs.count()

                # if length != 0:
                #     start_line = (current_page - 1) * length
                #     stop_line = start_line + length
                #     objs = objs[start_line: stop_line]

                ret_data = []
                for obj in objs:
                    ret_data.append({
                        'id': obj.user.id,
                        'username': obj.user.username,
                        'source': obj.get_source_display(),
                        'avatar': obj.user.avatar,
                        'company': obj.user.company.name,
                        'position': obj.user.position,
                        'email': obj.user.email or '',
                        'mingpian_phone': obj.user.mingpian_phone or '',  # 名片手机号
                        'create_date': obj.create_date,  # 创建时间
                    })

                response.code = 200
                response.msg = '查询成功'
                response.data = {
                    'ret_data': ret_data,
                    'data_count': count,
                }


            else:
                response.code = 402
                response.msg = "请求异常"
                response.data = json.loads(forms_obj.errors.as_json())

    else:
        response.code = 402
        response.msg = "请求异常"

    return JsonResponse(response.__dict__)



# 生成海报相关信息页面用于截图使用
@csrf_exempt
def mingpian_poster_html_oper(request):

    if request.method == 'GET':
        customer_id = request.GET.get('user_id')
        user_id = request.GET.get('uid')

        obj = models.zgld_userprofile.objects.get(id=user_id)

        user_photo_obj = models.zgld_user_photo.objects.filter(user_id=user_id, photo_type=2).order_by('-create_date')

        if user_photo_obj:
            user_avatar = "/" + user_photo_obj[0].photo_url

        else:
            if obj.avatar.startswith("http"):
                user_avatar = obj.avatar
            else:
                user_avatar = "/" + obj.avatar

        qr_code = ''
        if  user_id and customer_id :
             qr_obj = models.zgld_user_customer_belonger.objects.filter(user_id=user_id, customer_id=customer_id)
             if qr_obj:
                 qr_code =   qr_obj[0].qr_code
                 if not qr_code:
                     # 异步生成小程序和企业用户对应的小程序二维码
                     data_dict = {'user_id': user_id, 'customer_id': customer_id}

                     url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/create_user_or_customer_qr_code'
                     get_data = {
                         'data': json.dumps(data_dict)
                     }
                     print('--- 小程序二维码: get_data-->', get_data)

                     s = requests.session()
                     s.keep_alive = False  # 关闭多余连接
                     s.get(url, params=get_data)

                     # tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))  #

                 qr_code =  "/" + qr_obj[0].qr_code


             print('--- 从 customer_belonger 里 --->>qr_code',qr_code)

        elif user_id and  not customer_id:
             qr_code = obj.qr_code
             if not qr_code:
                 # 异步生成小程序和企业用户对应的小程序二维码
                 data_dict = {'user_id': user_id, 'customer_id': ''}
                 # tasks.create_user_or_customer_small_program_qr_code.delay(json.dumps(data_dict))  #

                 url = 'http://api.zhugeyingxiao.com/zhugeleida/mycelery/create_user_or_customer_qr_code'
                 get_data = {
                     'data': json.dumps(data_dict)
                 }
                 print('--- 小程序二维码: get_data-->', get_data)

                 s = requests.session()
                 s.keep_alive = False  # 关闭多余连接
                 s.get(url, params=get_data)

             qr_code = "/" +  obj.qr_code
             print('--- 从 zgld_userprofile 里 --->>qr_code',qr_code)

        ret_data = {
            'user_id': obj.id,
            'user_avatar': user_avatar,
            'username': obj.username,
            'position': obj.position,
            'mingpian_phone': obj.mingpian_phone,
            'company': obj.company.name,
            'qr_code_url': qr_code,
        }

        return render(request, 'create_poster.html', locals())


