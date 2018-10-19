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
from zhugeleida.forms.admin.activity_manage_verify import SetFocusGetRedPacketForm, ActivityAddForm, ActivitySelectForm,ActivityUpdateForm

import json
from django.db.models import Q,Sum



@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def activity_manage(request, oper_type):
    response = Response.ResponseObj()

    if request.method == "POST":

        # 设置关注领红包
        if oper_type == 'set_focus_get_redPacket':

            is_focus_get_redpacket = request.POST.get('is_focus_get_redpacket')
            focus_get_money = request.POST.get('focus_get_money')
            focus_total_money = request.POST.get('focus_total_money')
            user_id = request.GET.get('user_id')

            form_data = {
                'is_focus_get_redpacket': is_focus_get_redpacket,
                'focus_get_money': focus_get_money,
                'focus_total_money': focus_total_money,
            }

            forms_obj = SetFocusGetRedPacketForm(form_data)
            if forms_obj.is_valid():
                company_id = models.zgld_admin_userprofile.objects.get(id=user_id).company_id
                gongzhonghao_app_objs = models.zgld_gongzhonghao_app.objects.filter(company_id=company_id)

                if gongzhonghao_app_objs:
                    gongzhonghao_app_objs.update(
                        is_focus_get_redpacket=is_focus_get_redpacket,
                        focus_get_money=focus_get_money,
                        focus_total_money=focus_total_money
                    )
                    #  查询成功 返回200 状态码
                    response.code = 200
                    response.msg = '设置成功'

                else:
                    response.code = 301
                    response.msg = '公众号不存在'


            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())



    else:
        # 查询关注红包
        if oper_type == 'query_focus_get_redPacket':
            user_id = request.GET.get('user_id')
            company_id = request.GET.get('company_id')

            objs = models.zgld_gongzhonghao_app.objects.filter(company_id=company_id)

            if objs:
                obj = objs[0]
                is_focus_get_redpacket = obj.is_focus_get_redpacket
                focus_get_money = obj.focus_get_money
                focus_total_money = obj.focus_total_money
                #  查询成功 返回200 状态码
                response.data = {
                    'is_focus_get_redpacket': is_focus_get_redpacket,  # 关注领取红包是否(开启)
                    'focus_get_money': focus_get_money,  # 关注领取红包金额
                    'focus_total_money': focus_total_money  # 红包总金额
                }
                response.code = 200
                response.msg = '设置成功'

            else:
                response.code = 301
                response.msg = '公众号不存在'

        elif oper_type == 'activity_list':

            print('request.GET----->', request.GET)

            forms_obj = ActivitySelectForm(request.GET)
            if forms_obj.is_valid():
                print('----forms_obj.cleaned_data -->', forms_obj.cleaned_data)
                product_type = forms_obj.cleaned_data.get('product_type')

                # 如果为1 代表是公司的官网
                user_id = request.GET.get('user_id')
                company_id = forms_obj.cleaned_data.get('company_id')
                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-create_date')

                q1 = Q()
                q1.connector = 'and'
                q1.children.append(('company_id', company_id))

                search_activity_name = request.GET.get('activity_name')  # 当有搜索条件 如 搜索产品名称
                if search_activity_name:
                    q1.children.append(('activity_name__contains', search_activity_name))

                article_title = request.GET.get('article_title')  # 当有搜索条件 如 搜索产品名称
                if article_title:
                    q1.children.append(('article__title__contains', article_title))

                activity_id = request.GET.get('activity_id')  # 当有搜索条件 如 搜索产品名称
                if activity_id:
                    q1.children.append(('id', activity_id))


                search_activity_status = request.GET.get('status')  # 当有搜索条件 如 搜索上架或者不上架的

                if search_activity_status:
                    q1.children.append(('status', search_activity_status))  # (1,'已上架')

                print('-----q1---->>', q1)
                objs = models.zgld_article_activity.objects.select_related('article', 'company').filter(q1).order_by(order)
                count = objs.count()
                print('-----objs----->>', objs)

                if length != 0:
                    start_line = (current_page - 1) * length
                    stop_line = start_line + length
                    objs = objs[start_line: stop_line]

                ret_data = []
                if objs:
                    for obj in objs:

                        ret_data.append({
                            'article_id' : obj.article_id,
                            'article_title' : obj.article.title,
                            'company_id' : obj.company_id,

                            'activity_id' : obj.id,    #活动Id
                            'activity_name' : obj.activity_name,    #分享文章名称
                            'activity_total_money' :  obj.activity_total_money,   #活动总金额
                            'activity_single_money' : obj.activity_single_money,  #单个金额
                            'reach_forward_num' :  obj.reach_forward_num,  #达到多少次发红包
                            'already_send_redPacket_num' :  obj.already_send_redPacket_num or 0,  #已发放发红包个数[领取条件]
                            'status': obj.status,
                            'status_text': obj.get_status_display(),
                            'start_time' : obj.start_time.strftime('%Y-%m-%d %H:%M'),
                            'end_time' : obj.end_time.strftime('%Y-%m-%d %H:%M'),
                            'create_date' : obj.create_date.strftime('%Y-%m-%d %H:%M')
                        })

                #  查询成功 返回200 状态码
                response.code = 200
                response.msg = '查询成功'
                response.data = {
                    'ret_data': ret_data,
                    'data_count': count,
                }


            else:

                response.code = 301
                response.msg = "验证未通过"
                response.data = json.loads(forms_obj.errors.as_json())

        elif oper_type == 'send_activity_redPacket':

            company_id = request.GET.get('company_id')
            parent_id = request.GET.get('parent_id')
            article_id = request.GET.get('article_id')
            activity_id = request.GET.get('activity_id')

            forms_obj = ArticleSelectForm(request.GET)
            if forms_obj.is_valid():
                print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)

                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-create_date')  # 默认是最新内容展示 ，阅读次数展示read_count， 被转发次数forward_count
                user_id = request.GET.get('user_id')              # 默认是最新内容展示 ，阅读次数展示read_count， 被转发次数forward_count

                field_dict = {
                    'id': '',
                    # 'user_id' : '',
                    'status': '',  # 按状态搜索, (1,'已发'),  (2,'未发'),
                    # 【暂时不用】 按员工搜索文章、目前只显示出自己的文章
                    'title': '__contains',  # 按文章标题搜索
                }


                activity_redPacket_objs = models.zgld_activity_redPacket.objects.filter(
                                                                                        article_id=article_id,
                                                                                        activity_id=activity_id
                                                                                        )

                if activity_redPacket_objs: # 说明有人参加活动
                    ret_data = []
                    for obj in activity_redPacket_objs:

                        forward_read_num = models.zgld_article_to_customer_belonger.objects.filter(
                            customer_parent_id=obj.customer_id).values_list('customer_id').distinct().count()

                        forward_stay_time_dict = models.zgld_article_to_customer_belonger.objects.filter(
                            customer_parent_id=obj.customer_id).aggregate(forward_stay_time=Sum('stay_time'))

                        forward_stay_time = forward_stay_time_dict.get('forward_stay_time')
                        if not forward_stay_time:
                            forward_stay_time = 0

                        activity_redPacket_objs.update(
                            forward_read_count=forward_read_num,
                            forward_stay_time=forward_stay_time
                        )
                        activity_obj = models.zgld_article_activity.objects.get(id=activity_id)

                        reach_forward_num = activity_obj.reach_forward_num  # 达到多少次发红包(转发阅读后次数))
                        already_send_redPacket_num = obj.already_send_redPacket_num  # 已发放次数
                        send_redPacket_money = obj.send_redPacket_money  # 已发红包金额

                        if reach_forward_num != 0:  # 不能为0
                            forward_read_num = int(forward_read_num)
                            if forward_read_num >= reach_forward_num:  # 转发大于 阈值,达到可以条件

                                divmod_ret = divmod(forward_read_num, reach_forward_num)

                                shoudle_send_num = divmod_ret[0]
                                yushu = divmod_ret[1]

                                if shoudle_send_num > already_send_redPacket_num:
                                    print('---- 【满足发红包条件】forward_read_num[转发被查看数] | reach_forward_num[需满足的阈值] ----->>',
                                          forward_read_num, "|", reach_forward_num)
                                    print('---- 【满足发红包条件】shoudle_send_num[实发数] | already_send_redPacket_num[已发数] ----->>',
                                          shoudle_send_num, "|", reach_forward_num)
                                    app_objs = models.zgld_gongzhonghao_app.objects.filter(company_id=company_id)
                                    activity_single_money = activity_obj.activity_single_money
                                    activity_name = activity_obj.activity_name

                                    customer_obj = models.zgld_customer.objects.get(id=parent_id)

                        ##

                        print('----- obj.tags.values---->', obj.tags.values('id', 'name'))
                        ret_data.append({
                            'id': obj.id,
                            'title': obj.title,  # 文章标题
                            'status_code': obj.status,  # 状态
                            'status': obj.get_status_display(),  # 状态


                            'customer_username': obj.customer.username,  # 如果为原创显示,文章作者
                            'customer_headimgurl': obj.customer.headimgurl,  # 用户的头像
                            'customer_de': obj.customer.get_sex_display(),  # 用户的头像
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
                    response.code = 301
                    response.msg = '[无记录]活动发红包记录表'
                    print('------[无记录]活动发红包记录表 parent_id | article_id | activity_id ----->>', parent_id, '|',
                          article_id, "|", activity_id)

    return JsonResponse(response.__dict__)


@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def activity_manage_oper(request, oper_type, o_id):
    response = Response.ResponseObj()

    if request.method == "POST":
        # 删除-个人产品
        if oper_type == "delete":


            objs = models.zgld_article_activity.objects.filter(id=o_id,status__in=[1,3,4])

            if objs:
                objs.delete()
                response.code = 200
                response.msg = "删除成功"

            else:
                response.code = 301
                response.msg = '活动不存在或者正在进行中'


        elif oper_type == 'update':

            user_id = request.GET.get('user_id')
            company_id = request.GET.get('company_id')
            activity_id = o_id
            activity_name = request.POST.get('activity_name')
            article_id = request.POST.get('article_id')  # 文章ID
            activity_total_money = request.POST.get('activity_total_money')
            activity_single_money = request.POST.get('activity_single_money')
            reach_forward_num = request.POST.get('reach_forward_num')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            form_data = {

                'company_id': company_id,
                'activity_id': activity_id,  # 活动名称
                'activity_name': activity_name,  # 活动名称

                'article_id': article_id,  # 文章ID
                'activity_total_money': activity_total_money,  # 活动总金额(元)
                'activity_single_money': activity_single_money,  # 单个金额(元)
                'reach_forward_num': reach_forward_num,  # 达到多少次发红包(转发次数)
                'start_time': start_time,  # 达到多少次发红包(转发次数)
                'end_time': end_time,  # 达到多少次发红包(转发次数)
            }

            forms_obj = ActivityUpdateForm(form_data)
            if forms_obj.is_valid():


                objs = models.zgld_article_activity.objects.filter(id=activity_id,company_id=company_id)

                if objs:
                    objs.update(
                    article_id=article_id,
                    activity_name=activity_name.strip(),
                    activity_total_money=activity_total_money,
                    activity_single_money=activity_single_money,
                    reach_forward_num=reach_forward_num,
                    start_time=start_time,
                    end_time=end_time
                )

                response.code = 200
                response.msg = "添加成功"

            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 增加红包活动
        elif oper_type == "add":

            user_id = request.GET.get('user_id')
            company_id = request.GET.get('company_id')
            activity_name = request.POST.get('activity_name')
            article_id =  request.POST.get('article_id')  # 文章ID
            activity_total_money = request.POST.get('activity_total_money')
            activity_single_money = request.POST.get('activity_single_money')
            reach_forward_num = request.POST.get('reach_forward_num')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            form_data = {

                'company_id': company_id,
                'activity_name': activity_name,  # 活动名称
                'article_id': article_id,  # 文章ID
                'activity_total_money': activity_total_money,  # 活动总金额(元)
                'activity_single_money': activity_single_money,  # 单个金额(元)
                'reach_forward_num': reach_forward_num,  # 达到多少次发红包(转发次数)
                'start_time': start_time,  # 达到多少次发红包(转发次数)
                'end_time': end_time,  # 达到多少次发红包(转发次数)
            }

            forms_obj = ActivityAddForm(form_data)
            if forms_obj.is_valid():

                models.zgld_article_activity.objects.create(
                    article_id=article_id,
                    company_id=company_id,
                    activity_name=activity_name.strip(),
                    activity_total_money=activity_total_money,
                    activity_single_money=activity_single_money,
                    reach_forward_num=reach_forward_num,
                    start_time=start_time,
                    end_time=end_time
                )

                response.code = 200
                response.msg = "添加成功"

            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 修改活动状态
        elif oper_type == "change_artivity_status":
            print('-------change_status------->>', request.POST)
            status = request.POST.get('status')

            article_objs = models.zgld_article_activity.objects.filter(id=o_id)

            if article_objs:

                article_objs.update(
                    status=status
                )
                response.code = 200
                response.msg = "修改状态成功"


            else:

                response.code = 302
                response.msg = '活动不存在'

    return JsonResponse(response.__dict__)
