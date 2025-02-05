from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.gongzhonghao.article_verify import ArticleAddForm, ArticleSelectForm, ArticleUpdateForm, \
    MyarticleForm, StayTime_ArticleForm, Forward_ArticleForm, LocationForm, ReviewArticleForm, ArticleReviewSelectForm, \
    RecommendArticleSelectForm,PraiseArticleForm

from zhugeapi_celery_project import tasks
from zhugeleida.public.common import action_record

import json
from django.db.models import Q, F, Count
from zhugeleida.public.condition_com import conditionCom
import datetime, base64

import requests
from zhugeleida.views_dir.admin.open_weixin_gongzhonghao import create_authorizer_access_token


# 公众号查询文章
@csrf_exempt
# @account.is_token(models.zgld_admin_userprofile)
def article(request, oper_type):
    response = Response.ResponseObj()

    if request.method == "GET":
        # 获取参数 页数 默认1

        if oper_type == 'myarticle_list':

            forms_obj = ArticleSelectForm(request.GET)
            if forms_obj.is_valid():
                print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)

                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-create_date')  # 默认是最新内容展示 ，阅读次数展示read_count， 被转发次数forward_count
                user_id = request.GET.get('user_id')  # 默认是最新内容展示 ，阅读次数展示read_count， 被转发次数forward_count

                field_dict = {
                    'id': '',
                    # 'user_id' : '',
                    'status': '',  # 按状态搜索, (1,'已发'),  (2,'未发'),
                    # 【暂时不用】 按员工搜索文章、目前只显示出自己的文章
                    'title': '__contains',  # 按文章标题搜索
                }

                request_data = request.GET.copy()

                company_id = models.zgld_userprofile.objects.get(id=user_id).company_id
                q = conditionCom(request_data, field_dict)
                q.add(Q(**{'company_id': company_id}), Q.AND)

                tag_list = json.loads(request.GET.get('tags_list')) if request.GET.get('tags_list') else []
                if tag_list:
                    q.add(Q(**{'tags__in': tag_list}), Q.AND)

                objs = models.zgld_article.objects.select_related('user', 'company').filter(q).order_by(order)
                count = objs.count()

                if length != 0:
                    print('current_page -->', current_page)
                    start_line = (current_page - 1) * length
                    stop_line = start_line + length
                    objs = objs[start_line: stop_line]

                # 获取所有数据
                ret_data = []
                # 获取第几页的数据
                for obj in objs:
                    print('----- obj.tags.values---->', obj.tags.values('id', 'name'))
                    ret_data.append({
                        'id': obj.id,
                        'title': obj.title,  # 文章标题
                        'status_code': obj.status,  # 状态
                        'status': obj.get_status_display(),  # 状态
                        'source_code': obj.source,  # 状态
                        'source': obj.get_source_display(),  # 状态
                        'author': obj.user.username,  # 如果为原创显示,文章作者
                        'avatar': obj.user.avatar,  # 用户的头像
                        'read_count': obj.read_count,  # 被阅读数量
                        'forward_count': obj.forward_count,  # 被转发个数
                        'create_date': obj.create_date,  # 文章创建时间
                        'cover_url': obj.cover_picture,  # 文章图片链接
                        'tag_list': list(obj.tags.values('id', 'name')),
                        'insert_ads': json.loads(obj.insert_ads) if obj.insert_ads else ''  # 插入的广告语

                    })

                response.code = 200
                response.data = {
                    'ret_data': ret_data,
                    'data_count': count,
                }

            else:
                # print("验证不通过")
                print(forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

            return JsonResponse(response.__dict__)


    return JsonResponse(response.__dict__)


@csrf_exempt
@account.is_token(models.zgld_customer)
def article_oper(request, oper_type, o_id):
    response = Response.ResponseObj()
    import json
    if request.method == "POST":
        # 添加公众号文章
        # if oper_type == "add":
        #     article_data = {
        #         'user_id': request.GET.get('user_id'),
        #         'title': request.POST.get('title'),
        #         'summary': request.POST.get('summary'),
        #         'content': request.POST.get('content'),
        #         'cover_picture': request.POST.get('cover_picture'),
        #     }
        #
        #     forms_obj = ArticleAddForm(article_data)
        #
        #     if forms_obj.is_valid():
        #         print('======forms_obj.cleaned_data====>>', forms_obj.cleaned_data)
        #
        #         dict_data = {
        #             'user_id': request.GET.get('user_id'),
        #             'title': forms_obj.cleaned_data['title'],
        #             'summary': forms_obj.cleaned_data['summary'],
        #             'content': forms_obj.cleaned_data['content'],
        #             'cover_picture': forms_obj.cleaned_data['cover_picture'].strip(),
        #             'insert_ads': request.POST.get('insert_ads')
        #         }
        #
        #         obj = models.zgld_article.objects.create(**dict_data)
        #         tags_id_list = json.loads(request.POST.get('tags_id_list')) if request.POST.get('tags_id_list') else []
        #         if tags_id_list:
        #             obj.tags = tags_id_list
        #
        #         response.code = 200
        #         response.msg = "添加成功"
        #
        #     else:
        #         # print("验证不通过")
        #         print(forms_obj.errors)
        #         response.code = 301
        #         response.msg = json.loads(forms_obj.errors.as_json())
        #
        # # 删除公众号文章
        # elif oper_type == "delete":
        #     print('------delete o_id --------->>', o_id)
        #     user_id = request.GET.get('user_id')
        #     article_objs = models.zgld_article.objects.filter(id=o_id, user_id=user_id)
        #
        #     if article_objs:
        #         article_objs.delete()
        #         response.code = 200
        #         response.msg = "删除成功"
        #
        #     else:
        #         response.code = 302
        #         response.msg = '文章不存在'
        #
        # # 修改公众号文章
        # elif oper_type == "update":
        #     article_data = {
        #         'article_id': o_id,
        #         'user_id': request.GET.get('user_id'),
        #         'title': request.POST.get('title'),
        #         'summary': request.POST.get('summary'),
        #         'content': request.POST.get('content'),
        #         'cover_picture': request.POST.get('cover_picture'),
        #
        #     }
        #
        #     forms_obj = ArticleUpdateForm(article_data)
        #     if forms_obj.is_valid():
        #         dict_data = {
        #             'title': forms_obj.cleaned_data['title'],
        #             'summary': forms_obj.cleaned_data['summary'],
        #             'content': forms_obj.cleaned_data['content'],
        #             'cover_picture': forms_obj.cleaned_data['cover_picture'],
        #             'insert_ads': request.POST.get('insert_ads')
        #         }
        #         user_id = request.GET.get('user_id')
        #         article_id = forms_obj.cleaned_data['article_id']
        #         obj = models.zgld_article.objects.filter(
        #             id=article_id, user_id=user_id
        #         )
        #         obj.update(**dict_data)
        #
        #         tags_id_list = json.loads(request.POST.get('tags_id_list')) if request.POST.get('tags_id_list') else []
        #         if tags_id_list:
        #             obj[0].tags = tags_id_list
        #
        #         response.code = 200
        #         response.msg = "修改成功"
        #     else:
        #         # print("验证不通过")
        #         print(forms_obj.errors)
        #         response.code = 301
        #         response.msg = json.loads(forms_obj.errors.as_json())

        # 经纬度转换成 地理位置
        if oper_type == 'location_convert':
            x_num = request.POST.get('x_num')
            y_num = request.POST.get('y_num')

            # x_num = '34.264642646862'
            # y_num = '108.95108518068'
            request_data_dict = {
                'x_num': x_num,
                'y_num': y_num
            }
            customer_id = request.GET.get('user_id')
            forms_obj = LocationForm(request_data_dict)
            if forms_obj.is_valid():
                location = x_num + ',' + y_num

                url = 'http://api.map.baidu.com/geocoder/v2'
                ak = 'NLVvUqThVdf38Gkyb1kizrqRC2yxa7t7'
                real_url = url + '/?callback=renderReverse&location=' + location + '&output=json&pois=1&ak=' + ak
                req = requests.get(real_url)
                print('------ 【百度接口返回】---->>', req.text)
                ret = req.text[29:-1]
                print('-------【百度接口返回json.dump】--------->>', ret)

                data = json.loads(ret)
                formatted_address = data.get('result').get('formatted_address')
                country = data.get('result').get('addressComponent').get('country')
                province = data.get('result').get('addressComponent').get('province')
                city = data.get('result').get('addressComponent').get('city')
                print('---- 解析出的具体位置 formatted_address ----->>', formatted_address)  # 输出具体位置
                objs = models.zgld_customer.objects.filter(id=customer_id)
                if objs:
                    objs.update(
                        country=country,
                        province=province,
                        city=city,
                        formatted_address=formatted_address
                    )
                response.code = 200
                response.msg = '解析成功'

            else:
                print('------- 验证未能通过------->>', forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 评论文章功能
        elif oper_type == 'review_article':

            from_customer_id = request.GET.get('user_id')
            content = request.POST.get('content')

            request_data_dict = {
                'article_id': o_id,
                'content': content,  # 文章所属用户的ID
                'customer_id': from_customer_id,  # 文章所属用户的ID
            }

            forms_obj = ReviewArticleForm(request_data_dict)
            if forms_obj.is_valid():

                encodestr = base64.b64encode(content.encode('utf-8'))
                msg = str(encodestr, 'utf-8')

                create_data = {
                    'article_id': o_id,
                    'content': msg,
                    'from_customer_id': from_customer_id
                }
                obj = models.zgld_article_comment.objects.create(**create_data)

                response.code = 200
                response.msg = "记录成功"
            else:

                print('-------未能通过------->>', forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 点赞文章
        elif oper_type == 'praise_article':
            customer_id = request.GET.get('user_id')
            uid = request.GET.get('uid')

            article_id = o_id
            # status = request.POST.get('status')
            status = 1


            request_data_dict = {
                'article_id': article_id,
                'status': status,  # 文章所属用户的ID
                'uid': uid,  # 文章所属用户的ID
            }

            forms_obj = PraiseArticleForm(request_data_dict)
            if forms_obj.is_valid():

                create_data = {
                    'article_id': o_id,
                    'customer_id': customer_id,
                    'status': status,
                    'user_id': uid,  # 文章所属用户的ID
                }
                article_objs = models.zgld_article.objects.filter(id=o_id)
                article_up_down_objs = models.zgld_article_action.objects.filter(article_id=o_id,customer_id=customer_id,user_id=uid)
                if article_up_down_objs:
                    article_up_down_objs.update(
                        status=status
                    )
                    response.code = 200
                    response.msg = "点赞记录完成"
                    response.data = {
                        'up_count': article_objs[0].up_count,
                        'is_praise_article': 1,
                        'is_praise_article_text': '已赞此文章' #article_up_down_objs[0].get_status_display()
                    }
                else:
                    models.zgld_article_action.objects.create(**create_data)

                    if article_objs:
                        article_objs.update(
                            up_count=F('up_count') + 1
                        )
                    response.data = {
                        'up_count': article_objs[0].up_count,
                        'is_praise_article': 1,
                        'is_praise_article_text': '已赞此文章'
                    }
                    response.code = 200
                    response.msg = "记录成功"

                title = models.zgld_article.objects.get(id=article_id).title
                remark = '点赞了您的文章《%s》' % (title)
                data = request.GET.copy()
                data['action'] = 19
                action_record(data, remark)

            else:

                print('-------未能通过------->>', forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

    else:

        # 查看公众号文章详情
        if oper_type == 'myarticle':

            print('----- 公众号查看文章 request.GET myarticle----->>', request.GET)
            customer_id = request.GET.get('user_id')
            uid = request.GET.get('uid')
            parent_id = request.GET.get('pid')
            company_id = request.GET.get('company_id')
            # activity_id = request.GET.get('activity_id')

            request_data_dict = {
                'article_id': o_id,
                'uid': uid,  # 文章所属用户的ID
                'parent_id': parent_id
            }

            forms_obj = MyarticleForm(request_data_dict)
            if forms_obj.is_valid():
                # print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)

                article_id = forms_obj.cleaned_data.get('article_id')
                zgld_article_objs = models.zgld_article.objects.filter(id=article_id)

                obj = zgld_article_objs[0]
                insert_ads = json.loads(obj.insert_ads) if obj.insert_ads else ''  # 插入的广告语

                if insert_ads and insert_ads.get('mingpian'):
                    webchat_code = ''
                    product_function_type = ''
                    company_obj = ''
                    company_objs = models.zgld_company.objects.filter(id=company_id)

                    if company_objs:
                        company_obj = company_objs[0]
                        is_customer_unique = company_obj.is_customer_unique
                        product_function_type = company_obj.product_function_type

                        if is_customer_unique:  # 唯一性
                            objs = models.zgld_user_customer_belonger.objects.select_related('user').filter(
                                customer_id=customer_id,
                                user__company_id=company_id)
                            uid = objs[0].user_id  # 找到那个建立关系的人。
                    if uid:
                        mingpian_avatar_objs = models.zgld_user_photo.objects.select_related(
                            'user'
                        ).filter(
                            user_id=uid,
                            photo_type=2
                        ).order_by(
                            '-create_date')
                        mingpian_avatar = ''
                        zgld_userprofile_obj = models.zgld_userprofile.objects.get(id=uid)  # 获取企业微信中雷达AI分享出来文章对应用户的信息

                        if mingpian_avatar_objs:
                            mingpian_avatar = mingpian_avatar_objs[0].photo_url

                        else:
                            mingpian_avatar = zgld_userprofile_obj.avatar

                        if product_function_type == 3:  #
                            webchat_code = company_obj.xcx_qr_code

                        else:
                            webchat_code = zgld_userprofile_obj.qr_code

                        insert_ads['username'] = zgld_userprofile_obj.username
                        insert_ads['avatar'] = mingpian_avatar
                        insert_ads['phone'] = zgld_userprofile_obj.mingpian_phone
                        insert_ads['position'] = zgld_userprofile_obj.position
                        insert_ads['webchat_code'] = webchat_code  # 展示小程序的二维码
                    else:
                        # 如果是预览默认写死
                        insert_ads['username'] = '张三'
                        insert_ads['avatar'] = 'statics/imgs/setAvator.jpg'
                        insert_ads['phone'] = '18888888888'
                        insert_ads['position'] = '经理'              # 职位
                        insert_ads['webchat_code'] = webchat_code    # 展示小程序的二维码
                # 获取所有数据
                ret_data = []
                # 获取第几页的数据

                tag_list = list(obj.tags.values('id', 'name'))
                # print('-----obj.tags.values---->', tag_list)
                title = obj.title

                article_up_down_objs = models.zgld_article_action.objects.filter(article_id=o_id,
                                                                                 customer_id=customer_id)
                if article_up_down_objs:
                    is_praise_article_text = '已赞此文章'
                    is_praise_article =  1
                else:
                    is_praise_article_text = '未赞此文章'
                    is_praise_article = 0

                ret_data.append({
                    'id': obj.id,
                    'title': title,  # 文章标题
                    'author': obj.user.username,  # 如果为原创显示,文章作者
                    'avatar': obj.user.avatar,  # 用户的头像
                    'summary': obj.summary,  # 摘要
                    'create_date': obj.create_date.strftime('%Y-%m-%d %H:%M:%S'),  # 文章创建时间
                    'cover_url': obj.cover_picture,  # 文章图片链接
                    'up_count': obj.up_count,  # 文章内容
                    'is_praise_article_text' : is_praise_article_text,
                    'is_praise_article' :  is_praise_article,
                    'content': obj.content,  # 文章内容
                    'tag_list': tag_list,
                    'insert_ads': insert_ads
                })

                article_access_log_id = ''
                if customer_id and uid:  ## 说明是客户查看了这个雷达用户分享出来的，uid为空说明是后台预览分享的，不要做消息提示了

                    q = Q()
                    q.add(Q(**{'article_id': article_id}), Q.AND)
                    q.add(Q(**{'customer_id': customer_id}), Q.AND)
                    q.add(Q(**{'user_id': uid}), Q.AND)

                    reach_forward_num = ''
                    activity_single_money = ''

                    _start_time = ''
                    _end_time = ''
                    is_have_activity = 2  # 默认没有搞活动

                    activity_objs = models.zgld_article_activity.objects.filter(article_id=article_id).exclude(
                        status=3).order_by('-create_date')
                    now_date_time = datetime.datetime.now()
                    is_limit_area = ''
                    reach_stay_time = ''
                    activity_id = ''
                    activity_mode = ''
                    if activity_objs:
                        activity_obj = activity_objs[0]
                        start_time = activity_obj.start_time
                        end_time = activity_obj.end_time
                        is_limit_area = activity_obj.is_limit_area
                        reach_stay_time = activity_obj.reach_stay_time
                        activity_mode = activity_obj.mode

                        if now_date_time >= start_time and now_date_time <= end_time:  # 活动开启并活动在进行中
                            _start_time = start_time.strftime('%Y-%m-%d %H:%M')
                            _end_time = end_time.strftime('%Y-%m-%d %H:%M')
                            activity_id = activity_obj.id
                            reach_forward_num = activity_obj.reach_forward_num
                            activity_single_money = activity_obj.activity_single_money

                            is_have_activity = 1  # 活动已经开启

                            if parent_id:
                                _data = {
                                    'customer_id': customer_id,
                                    'user_id': uid,
                                    'parent_id': parent_id,
                                    'article_id': article_id,
                                    'activity_id': activity_id,
                                    'company_id': company_id,
                                }  ## 判断转发后阅读的人数 +转发后阅读时间 此处封装到异步中。
                                tasks.user_forward_send_activity_redPacket.delay(_data)

                                # 说明被人转发后有人查看后,发送公众号模板消息给他的父亲级，提示他有人查看了他的文章
                                data_ = {
                                    'parent_id': parent_id,
                                    'customer_id': customer_id,
                                    'user_id': uid,
                                    'activity_id': activity_id,
                                    'type': 'forward_look_article_tishi'
                                }
                                print('--- 【公众号发送模板消息】 user_send_gongzhonghao_template_msg --->', data_)

                                tasks.user_send_gongzhonghao_template_msg.delay(data_)  # 发送【公众号发送模板消息】

                    if parent_id:
                        q.add(Q(**{'customer_parent_id': parent_id}), Q.AND)

                    else:
                        q.add(Q(**{'customer_parent_id__isnull': True}), Q.AND)

                    now_date_time = datetime.datetime.now()
                    customer_objs = models.zgld_customer.objects.filter(id=customer_id, user_type=1)
                    # zgld_article_objs.update(status=1)  # 改为已发状态
                    zgld_article_objs.update(read_count=F('read_count') + 1)  # 文章阅读数量+1，针对所有的雷达用户来说
                    models.zgld_article_to_customer_belonger.objects.filter(q).update(
                        read_count=F('read_count') + 1,
                        last_access_date=now_date_time
                    )

                    is_subscribe = ''
                    is_subscribe_text = ''
                    if customer_objs:
                        customer_obj = customer_objs[0]
                        username = customer_obj.username
                        is_subscribe = customer_obj.is_subscribe
                        is_subscribe_text = customer_obj.get_is_subscribe_display()

                        if username:
                            remark = '%s》,看来对您的文章感兴趣' % (('正在查看文章《' + title))
                            print('---- 公众号查看文章[消息提醒]--->>', remark)
                            data = request.GET.copy()
                            data['action'] = 14
                            data['article_id'] = obj.id
                            action_record(data, remark)  # 此步骤封装到 异步中。

                    ## 记录一个用户查看文章的日志
                    article_access_log_obj = models.zgld_article_access_log.objects.create(
                        article_id=article_id,
                        customer_id=customer_id,
                        user_id=uid,
                        customer_parent_id=parent_id,
                        last_access_date=now_date_time
                    )
                    article_access_log_id = article_access_log_obj.id

                    qrcode_url = ''
                    is_focus_get_redpacket = 2  # 默认是不开启关注领红包
                    focus_get_money = ''
                    gongzhonghao_mode = ''
                    gongzhonghao_name = ''
                    is_open_comment_text = ''
                    is_open_comment = ''
                    gongzhonghao_app_objs = models.zgld_gongzhonghao_app.objects.filter(company_id=company_id)
                    if gongzhonghao_app_objs:
                        gongzhonghao_app_obj = gongzhonghao_app_objs[0]
                        qrcode_url = gongzhonghao_app_obj.qrcode_url
                        gongzhonghao_mode = gongzhonghao_app_obj.mode
                        gongzhonghao_name = gongzhonghao_app_obj.name
                        is_open_comment = gongzhonghao_app_obj.is_open_comment
                        is_open_comment_text = gongzhonghao_app_obj.get_is_open_comment_display()

                        is_focus_get_redpacket = gongzhonghao_app_obj.is_focus_get_redpacket
                        if is_focus_get_redpacket:
                            focus_get_money = gongzhonghao_app_obj.focus_get_money
                            is_focus_get_redpacket = 1

                    response.code = 200
                    response.data = {
                        'ret_data': ret_data,
                        'article_access_log_id': article_access_log_id,
                        'activity_id': activity_id,
                        'is_focus_get_redpacket': is_focus_get_redpacket,  # 关注领取红包是否开启。 'true' 或   'false'
                        'focus_get_money': focus_get_money,  # 关注领取红包金额
                        'is_subscribe': is_subscribe,  # 是否关注了公众号。0 为没有关注 1为关注了。
                        'is_subscribe_text': is_subscribe_text,
                        'is_have_activity': is_have_activity,  # 是否搞活动。0 是没有活动，1 是活动已经开启。
                        'qrcode_url': qrcode_url,
                        'is_limit_area': is_limit_area,
                        'reach_stay_time': reach_stay_time,
                        'reach_forward_num': reach_forward_num,  # 达到多少次发红包
                        'activity_single_money': activity_single_money,  # 单个金额
                        'start_time': _start_time,
                        'end_time': _end_time,

                        'is_open_comment_text': is_open_comment_text,
                        'is_open_comment': is_open_comment,
                        'gongzhonghao_mode': gongzhonghao_mode,
                        'activity_mode': activity_mode,
                        'gongzhonghao_name': gongzhonghao_name
                    }

                else:
                    response.code = 200
                    response.msg = '没有customer_id'
                    response.data = {
                        'ret_data': ret_data,
                        'article_access_log_id': article_access_log_id,
                    }

            else:
                print('------- 公众号查看我的文章未能通过------->>', forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

            return JsonResponse(response.__dict__)

        # 文章评论列表展示
        elif oper_type == 'article_review_list':

            customer_id = request.GET.get('user_id')
            form_data = {
                'article_id': o_id
            }
            forms_obj = ArticleReviewSelectForm(form_data)

            if forms_obj.is_valid():
                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']

                objs = models.zgld_article_comment.objects.select_related('from_customer', 'to_customer').filter(
                    article_id=o_id).filter(Q(is_audit_pass=1) | Q(from_customer=customer_id)).order_by('-create_date')

                count = objs.count()
                if objs:

                    # if length != 0:
                    #     start_line = (current_page - 1) * length
                    #     stop_line = start_line + length
                    #     objs = objs[start_line: stop_line]

                    ret_data = []
                    for obj in objs:

                        try:
                            username = base64.b64decode(obj.from_customer.username)
                            customer_name = str(username, 'utf-8')
                            print('----- 解密b64decode username----->', username)
                        except Exception as e:
                            print('----- b64decode解密失败的 customer_id 是 | e ----->', obj.from_customer_id, "|", e)
                            customer_name = '客户ID%s' % (obj.from_customer_id)

                        _content = base64.b64decode(obj.content)
                        content = str(_content, 'utf-8')
                        print('----- 解密b64decode 内容content----->', content)

                        ret_data.append({
                            'from_customer_id': obj.from_customer_id,
                            'from_customer_name': customer_name,
                            'from_customer_headimgurl': obj.from_customer.headimgurl,
                            'content': content,
                            'create_time': obj.create_date.strftime('%Y-%m-%d %H:%M:%S')
                        })

                    response.code = 200
                    response.msg = '查询成功'
                    response.data = {
                        'ret_data': ret_data,
                        'data_count': count,
                    }

                else:
                    response.code = 302
                    response.msg = '没有数据'

            else:
                response.code = 402
                response.msg = "请求异常"
                response.data = json.loads(forms_obj.errors.as_json())

        # 推荐的文章列表
        elif oper_type == 'recommend_article_list':
            customer_id = request.GET.get('user_id')
            uid = request.GET.get('uid')
            company_id = request.GET.get('company_id')

            form_data = {
                'article_id': o_id,
                'company_id': company_id,
                'uid': uid
            }
            forms_obj = RecommendArticleSelectForm(form_data)

            if forms_obj.is_valid():

                objs = models.zgld_article.objects.select_related('user', 'company').filter(status=1,company_id=company_id).exclude(id=o_id).order_by(
                    '-read_count')

                count = objs.count()
                if objs:

                    objs = objs[0:3]
                    ret_data = []
                    for obj in objs:
                        _data = {
                            'article_id': obj.id,
                            'uid': uid,  # 雷达用户ID。
                            'company_id': company_id
                        }
                        article_url = create_gongzhonghao_share_auth_url(_data)

                        ret_data.append({
                            'article_id': obj.id,
                            'title': obj.title,
                            'article_url': article_url,
                            'read_count': obj.read_count,
                            'create_date': obj.create_date.strftime('%Y-%m-%d %H:%M:%S')
                        })

                    response.code = 200
                    response.msg = '查询成功'
                    response.data = {
                        'ret_data': ret_data,
                        'data_count': count,
                    }

                else:
                    response.code = 302
                    response.msg = '没有数据'

            else:
                response.code = 402
                response.msg = "请求异常"
                response.data = json.loads(forms_obj.errors.as_json())

        # 转发公众号文章
        elif oper_type == 'forward_article':

            uid = request.GET.get('uid')
            customer_id = request.GET.get('user_id')
            parent_id = request.GET.get('pid')
            forward_type = request.GET.get('forward_type')

            request_data_dict = {
                'article_id': o_id,
                'uid': uid,  # 文章所属用户的ID
                'customer_id': customer_id,  # 文章所属用户的ID
                'forward_type': forward_type,  # 文章所属用户的ID

            }

            forms_obj = Forward_ArticleForm(request_data_dict)
            if forms_obj.is_valid():
                article_id = o_id
                forward_type = forms_obj.cleaned_data.get('forward_type')

                objs = models.zgld_article.objects.filter(id=article_id)
                objs.update(forward_count=F('forward_count') + 1)  #

                if uid:
                    q = Q()
                    q.add(Q(**{'article_id': article_id}), Q.AND)
                    q.add(Q(**{'customer_id': customer_id}), Q.AND)
                    q.add(Q(**{'user_id': uid}), Q.AND)

                    if parent_id:
                        q.add(Q(**{'customer_parent_id': parent_id}), Q.AND)
                    else:
                        q.add(Q(**{'customer_parent_id__isnull': True}), Q.AND)

                    models.zgld_article_to_customer_belonger.objects.filter(q).update(
                        forward_count=F('forward_count') + 1)

                    action = ''
                    place = ''
                    if int(forward_type) == 1:  # 1 转发朋友
                        action = 15
                        place = '分享给【朋友】'
                        models.zgld_article_to_customer_belonger.objects.filter(q).update(
                            forward_friend_count=F('forward_friend_count') + 1)

                    elif int(forward_type) == 2:  # 3转发朋友圈
                        action = 16
                        place = '分享到【朋友圈】'
                        models.zgld_article_to_customer_belonger.objects.filter(q).update(
                            forward_friend_circle_count=F('forward_friend_circle_count') + 1)

                    remark = '转发了您的文章《%s》%s,帮您进一步扩大了传播效果' % (objs[0].title, place)
                    data = request.GET.copy()
                    data['action'] = action
                    data['article_id'] = o_id
                    action_record(data, remark)
                    response.code = 200
                    response.msg = "记录转发文章成功"
            else:

                print('------- 公众号-转发文章未能通过------->>', forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 记录客户查看文章时间
        elif oper_type == 'staytime':
            uid = request.GET.get('uid')
            customer_id = request.GET.get('user_id')
            parent_id = request.GET.get('pid')
            article_access_log_id = request.GET.get('article_access_log_id')
            reach_stay_time = request.GET.get('reach_stay_time')

            activity_id = request.GET.get('activity_id')
            is_have_activity = request.GET.get('is_have_activity')

            request_data_dict = {
                'article_id': o_id,
                'uid': uid,  # 文章所属用户的ID
                'customer_id': customer_id,  # 文章所属用户的ID
                'parent_id': parent_id,  # 文章所属用户的ID
                'article_access_log_id': article_access_log_id,  # 文章日志ID
            }

            forms_obj = StayTime_ArticleForm(request_data_dict)
            if forms_obj.is_valid():
                article_id = o_id
                if uid:  # 说明是雷达客户分享出去的文章
                    q = Q()
                    q.add(Q(**{'article_id': article_id}), Q.AND)
                    q.add(Q(**{'customer_id': customer_id}), Q.AND)
                    q.add(Q(**{'user_id': uid}), Q.AND)

                    if parent_id:
                        q.add(Q(**{'customer_parent_id': parent_id}), Q.AND)
                    else:
                        q.add(Q(**{'customer_parent_id__isnull': True}), Q.AND)
                    # print('查询值 q--->>', q)
                    objs = models.zgld_article_to_customer_belonger.objects.select_related('article').filter(q)
                    if objs:
                        obj = objs[0]
                        objs.update(stay_time=F('stay_time') + 5)  #

                        company_id = ''
                        userprofile_objs = models.zgld_userprofile.objects.filter(id=uid)
                        if userprofile_objs:
                            company_id = userprofile_objs[0].company_id

                        ### 自动打标签
                        tags_time_count = obj.article.tags_time_count
                        stay_time = obj.stay_time

                        if stay_time >= tags_time_count:
                            tags_name_list = list(obj.article.tags.all().values_list('name', flat=True))

                            # 方法1
                            customer_obj = models.zgld_customer.objects.get(id=customer_id)
                            already_tag_name_list = list(
                                customer_obj.zgld_tag_set.all().values_list('name', flat=True))  # 此客户已经拥有的标签

                            already_tag_list = ''
                            already_company_tags_name_list = ''
                            for tag_name in tags_name_list:

                                if tag_name in already_tag_name_list:  # 满足 文章标签已经在 【客户标签列表中】就不用创建
                                    # print('tag_name 文章标签已经在 【客户标签列表中】---------->>', tag_name, "|",
                                    #       already_tag_name_list)
                                    continue

                                elif not already_tag_list:
                                    # print('值 already_tag_list 为空 ------>>')
                                    already_tag_list = list(
                                        customer_obj.zgld_tag_set.all().values_list('id', flat=True))
                                    already_company_tags_name_list = list(models.zgld_tag.objects.filter(user_id=uid,
                                                                                                         user__company_id=company_id).values_list(
                                        'name', flat=True))

                                tag_data = {
                                    'name': tag_name,
                                    'user_id': uid,
                                    'tag_type': 1  # (1, '微信公众号'),
                                }
                                # print('值 already_tag_list-------->', already_tag_list)

                                if tag_name not in already_company_tags_name_list:
                                    parent_id = models.zgld_tag.objects.filter(name='自定义')[0].id
                                    _obj = models.zgld_tag.objects.create(**tag_data)
                                    _obj.tag_parent_id = parent_id
                                    _obj.save()
                                    tag_id = _obj.id


                                else:
                                    _objs = models.zgld_tag.objects.filter(name=tag_name, user_id=uid,
                                                                           user__company_id=company_id)
                                    _obj = _objs[0]
                                    tag_id = _obj.id

                                if str(tag_id) not in already_tag_list:
                                    already_tag_list.append(str(tag_id))

                            if already_tag_list:
                                now_tag_list = [int(i) for i in already_tag_list]

                                # print('值 now_tag_list ----->>', now_tag_list)

                                if customer_obj:
                                    customer_obj.zgld_tag_set = now_tag_list

                            '''
                            # 操作tag，为客户添加多个标签
                            elif oper_type == "customer_tag":
                    
                                tag_list = json.loads(request.POST.get('tag_list'))
                                customer_obj = models.zgld_customer.objects.get(id=o_id)
                    
                                if customer_obj:
                                    customer_obj.zgld_tag_set = tag_list
                                    response.code = 200
                                    response.msg = "添加成功"
                            '''

                        article_access_log_objs = models.zgld_article_access_log.objects.filter(
                            id=article_access_log_id)
                        now_date_time = datetime.datetime.now()
                        if article_access_log_objs:
                            article_access_log_objs.update(
                                stay_time=F('stay_time') + 5,
                                last_access_date=now_date_time
                            )
                            # 'is_have_activity': is_have_activity,  # 是否搞活动。0 是没有活动，1 是活动已经开启。
                            is_have_activity = int(is_have_activity) if is_have_activity else ''
                            reach_stay_time = int(reach_stay_time) if reach_stay_time else ''

                            if activity_id and is_have_activity == 1 and reach_stay_time != 0:
                                # print('------- 此文章有【活动开启】并【有时间限制: %s】 ------>>' % (reach_stay_time))
                                activity_objs = models.zgld_article_activity.objects.filter(
                                    article_id=article_id).exclude(
                                    status=3).order_by('-create_date')
                                now_date_time = datetime.datetime.now()
                                is_limit_area = ''
                                if activity_objs:
                                    activity_obj = activity_objs[0]
                                    start_time = activity_obj.start_time
                                    end_time = activity_obj.end_time
                                    reach_stay_time = activity_obj.reach_stay_time

                                    # print('库值 start_time------>>', start_time)
                                    # print('库值 end_time------>>', end_time)
                                    # print('库值 reach_stay_time------>>', reach_stay_time)

                                    if now_date_time >= start_time and now_date_time <= end_time:
                                        # print('活动开启并活动在进行中 -------->>')

                                        article_access_log_obj = article_access_log_objs[0]

                                        if reach_stay_time != 0:  # 0 代表 没有时间限制
                                            stay_time = article_access_log_obj.stay_time
                                            # print('库值 stay_time-------->', stay_time)
                                            # print('库值 reach_stay_time-------->', reach_stay_time)

                                            if stay_time >= reach_stay_time:

                                                if parent_id:
                                                    # company_id = ''
                                                    # userprofile_objs = models.zgld_userprofile.objects.filter(id=uid)
                                                    # if userprofile_objs:
                                                    #     company_id = userprofile_objs[0].company_id

                                                    _data = {
                                                        'article_access_log_id': article_access_log_id,
                                                        'customer_id': customer_id,
                                                        'user_id': uid,
                                                        'parent_id': parent_id,
                                                        'article_id': article_id,
                                                        'activity_id': activity_id,
                                                        'company_id': company_id,
                                                    }  ## 判断转发后阅读的人数 +转发后阅读时间 此处封装到异步中。
                                                    # print('传输异步数据 tasks json.dumps(_data) --------->>',
                                                    #       json.dumps(_data))

                                                    tasks.user_forward_send_activity_redPacket.delay(_data)

                    else:
                        pass
                        # print('无关系 article_to_customer_belonger -------->>', q)

                    response.code = 200
                    response.msg = "记录客户查看文章时间成功"

            else:
                # print('------- 公众号-记录查看文章时间未能通过------->>', forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 获取用户信息
        elif oper_type == 'test_send_redPacket':

            # _data = {
            #
            #     'parent_id': 9,
            #     'article_id': 23,
            #     'activity_id': 1,
            #     'company_id': 1,
            # }
            #
            # tasks.user_forward_send_activity_redPacket.delay(_data)

            three_service_objs = models.zgld_three_service_setting.objects.filter(three_services_type=2)  # 公众号
            qywx_config_dict = ''
            if three_service_objs:
                three_service_obj = three_service_objs[0]
                qywx_config_dict = three_service_obj.config
                if qywx_config_dict:
                    qywx_config_dict = json.loads(qywx_config_dict)

            app_id = qywx_config_dict.get('app_id')
            app_secret = qywx_config_dict.get('app_secret')

            _data = {
                'authorizer_appid': 'wxa77213c591897a13',
                'authorizer_refresh_token': 'refreshtoken@@@RAVUheyR510HyjAYrDxgSrX8MHDkbbb5ysHgGRWHeUc',
                'key_name': 'authorizer_access_token_wxa77213c591897a13',
                'app_id': app_id,  # 'wx6ba07e6ddcdc69b3',                     # 查看诸葛雷达_公众号的 appid
                'app_secret': app_secret  # '0bbed534062ceca2ec25133abe1eecba'    # 查看诸葛雷达_公众号的AppSecret
            }

            authorizer_access_token_ret = create_authorizer_access_token(_data)
            authorizer_access_token = authorizer_access_token_ret.data

            # access_token = "14_8p_bIh8kVgaZpnn_8IQ3y77mhJcSLoLuxnqtrE-mKYuOfXFPnNYhZAOWk8AZ-NeK6-AthHxolrSOJr1HvlV-gSlspaO0YFYbkPrsjJzKxalWQtlBxX4n-v11mqJElbT0gn3WVo9UO5zQpQMmTDGjAEDZJM"
            openid = 'ob5mL1Q4faFlL2Hv2S43XYKbNO-k'

            # get_user_info_url = 'https://api.weixin.qq.com/sns/userinfo'
            get_user_info_url = 'https://api.weixin.qq.com/cgi-bin/user/info'
            get_user_info_data = {
                'access_token': authorizer_access_token,
                'openid': openid,
                'lang': 'zh_CN',
            }

            s = requests.session()
            s.keep_alive = False  # 关闭多余连接
            ret = s.get(get_user_info_url, params=get_user_info_data)

            # ret = requests.get(get_user_info_url, params=get_user_info_data)
            ret.encoding = 'utf-8'
            ret_json = ret.json()

            print('----------- 【公众号】拉取用户信息 接口返回 ---------->>', json.dumps(ret_json))

    return JsonResponse(response.__dict__)


def create_gongzhonghao_share_auth_url(data):
    uid = data.get('uid')  # 雷达用户ID。代表此企业用户从雷达里分享出去-这个文章。
    article_id = data.get('article_id')
    company_id = data.get('company_id')

    three_service_objs = models.zgld_three_service_setting.objects.filter(three_services_type=2)  # 公众号
    qywx_config_dict = ''
    if three_service_objs:
        three_service_obj = three_service_objs[0]
        qywx_config_dict = three_service_obj.config
        if qywx_config_dict:
            qywx_config_dict = json.loads(qywx_config_dict)

    api_url = qywx_config_dict.get('api_url')

    pid = ''
    level = 1
    redirect_uri = '%s/zhugeleida/gongzhonghao/work_gongzhonghao_auth?relate=article_id_%s|pid_%s|level_%s|uid_%s|company_id_%s' % (
        api_url, article_id, pid, level, uid, company_id)

    # token = qywx_config_dict.get('token')
    # encodingAESKey = qywx_config_dict.get('encodingAESKey')

    print('--------  嵌入创建【分享链接】的 redirect_uri ------->', redirect_uri)

    scope = 'snsapi_userinfo'  # snsapi_userinfo （弹出授权页面，可通过openid拿到昵称、性别、所在地。并且， 即使在未关注的情况下，只要用户授权，也能获取其信息 ）
    state = 'snsapi_base'

    three_service_objs = models.zgld_three_service_setting.objects.filter(three_services_type=2)  # 公众号
    qywx_config_dict = ''
    if three_service_objs:
        three_service_obj = three_service_objs[0]
        qywx_config_dict = three_service_obj.config
        if qywx_config_dict:
            qywx_config_dict = json.loads(qywx_config_dict)

    component_appid = qywx_config_dict.get('app_id')
    gongzhonghao_app_obj = models.zgld_gongzhonghao_app.objects.get(company_id=company_id)
    authorization_appid = gongzhonghao_app_obj.authorization_appid

    # component_appid = 'wx6ba07e6ddcdc69b3' # 三方平台-AppID
    appid = authorization_appid
    share_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s&component_appid=%s#wechat_redirect' % (
        appid, redirect_uri, scope, state, component_appid)

    from urllib.parse import quote
    bianma_share_url = quote(share_url, 'utf-8')

    three_service_objs = models.zgld_three_service_setting.objects.filter(three_services_type=2)  # 公众号
    qywx_config_dict = ''
    if three_service_objs:
        three_service_obj = three_service_objs[0]
        qywx_config_dict = three_service_obj.config
        if qywx_config_dict:
            qywx_config_dict = json.loads(qywx_config_dict)

    leida_http_url = qywx_config_dict.get('authorization_url')
    share_url = '%s/zhugeleida/gongzhonghao/work_gongzhonghao_auth/redirect_share_url?share_url=%s' % (
    leida_http_url, bianma_share_url)

    print('------ 【雷达企业用户】正在触发【创建分享链接】 静默方式的 snsapi_base URL：------>>', share_url)

    return share_url
