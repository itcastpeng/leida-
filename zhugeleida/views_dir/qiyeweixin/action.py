from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.xiaochengxu.action_verify import ActionSelectForm, ActionCountForm, ActionCustomerForm
from zhugeleida import models

from django.db.models import Count
from publicFunc.condition_com import conditionCom
from django.db.models import Q
from datetime import datetime, timedelta
import base64

@csrf_exempt
@account.is_token(models.zgld_userprofile)
def action(request, oper_type):
    '''
     分页获取访问的全部日志信息
    :param request:
    :return:
    '''
    if request.method == 'GET':
        if oper_type == 'time':
            forms_obj = ActionSelectForm(request.GET)
            if forms_obj.is_valid():
                response = Response.ResponseObj()
                user_id = request.GET.get('user_id')
                customer_id = request.GET.get('customer_id')

                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-create_date')

                field_dict = {
                    'id': '',
                    'action': '',

                }

                q = conditionCom(request, field_dict)
                q.add(Q(**{'user_id': user_id}), Q.AND)
                if customer_id:
                    q.add(Q(**{'customer_id': customer_id}), Q.AND)
                create_date__gte = request.GET.get('create_date__gte')
                create_date__lt = request.GET.get('create_date__lt')
                action = request.GET.get('action')

                if action:  # 表示是行为中的请求
                    if not create_date__gte:
                        now_time = datetime.now()
                        create_date__gte = (now_time - timedelta(days=7)).strftime("%Y-%m-%d")
                        q.add(Q(**{'create_date__gte': create_date__gte}), Q.AND)

                    if create_date__lt:
                        stop_time = (datetime.strptime(create_date__lt, '%Y-%m-%d') + timedelta(days=1)).strftime(
                            "%Y-%m-%d")
                        q.add(Q(**{'create_date__lt': stop_time}), Q.AND)

                objs = models.zgld_accesslog.objects.select_related('user', 'customer').filter(q).order_by(order)
                objs.update(is_new_msg=False)

                count = objs.count()

                if length != 0:
                    start_line = (current_page - 1) * length
                    stop_line = start_line + length
                    objs = objs[start_line: stop_line]

                ret_data = []
                for obj in objs:

                    username = base64.b64decode(obj.customer.username)
                    username = str(username, 'utf-8')
                    print('-----b64decode username----->', username)

                    ret_data.append({
                        'user_id': obj.user_id,
                        'customer_id': obj.customer_id,
                        'headimgurl': obj.customer.headimgurl,
                        'log': username + obj.remark,
                        'create_date': obj.create_date,
                    })

                if current_page == 1:
                    count_action_data = models.zgld_accesslog.objects.filter(user_id=user_id).values('action').annotate(
                        Count('action'))
                    print('count_action_data -->', count_action_data)

                    customer_action_data = models.zgld_accesslog.objects.filter(user_id=user_id).values('action',
                                                                                                        'customer_id',
                                                                                                        'customer__username').annotate(
                        Count('action'))
                    print('customer_action_data -->', customer_action_data)

                response.code = 200
                response.msg = '查询日志记录成功'
                response.data = {
                    'ret_data': ret_data,
                    'data_count': count,
                }

                return JsonResponse(response.__dict__)

        elif oper_type == 'get_new_log':
            forms_obj = ActionSelectForm(request.GET)
            if forms_obj.is_valid():
                response = Response.ResponseObj()

                order = request.GET.get('order', '-create_date')

                field_dict = {
                    'user_id': '',
                    'action': '',
                }

                q = conditionCom(request, field_dict)
                q.add(Q(**{'is_new_msg': True}), Q.AND)
                print('---action---->>',q)

                objs = models.zgld_accesslog.objects.select_related('user', 'customer').filter(q).order_by(order)
                count = objs.count()

                ret_data = []
                for obj in objs:
                    username = base64.b64decode(obj.customer.username)
                    username = str(username, 'utf-8')
                    print('-----b64decode username----->', username)

                    ret_data.append({
                        'user_id': obj.user_id,
                        'customer_id': obj.customer_id,
                        'action' : obj.get_action_display(),
                        'log': username + obj.remark,
                        'create_date': obj.create_date,
                    })

                print('----ret_data----->>', ret_data)
                objs.update(is_new_msg=False)
                response.code = 200
                response.msg = '查询日志记录成功'
                response.data = {
                    'ret_data': ret_data,
                    'data_count': count,
                }

                return JsonResponse(response.__dict__)

        elif oper_type == 'count':
            forms_obj = ActionCountForm(request.GET)
            if forms_obj.is_valid():
                response = Response.ResponseObj()
                user_id = request.GET.get('user_id')

                field_dict = {
                    'id': '',
                    'user_id': '',
                    'create_date__gte': '',
                    # 'create_date__lt': '',

                }

                q = conditionCom(request, field_dict)

                create_date__gte = request.GET.get('create_date__gte')
                create_date__lt = request.GET.get('create_date__lt')
                if not create_date__gte:
                    now_time = datetime.now()
                    create_date__gte = (now_time - timedelta(days=7)).strftime("%Y-%m-%d")
                    q.add(Q(**{'create_date__gte': create_date__gte}), Q.AND)

                if create_date__lt:
                    stop_time = (datetime.strptime(create_date__lt, '%Y-%m-%d') + timedelta(days=1)).strftime(
                        "%Y-%m-%d")
                    q.add(Q(**{'create_date__lt': stop_time}), Q.AND)

                print('q  ---->', q)

                objs = models.zgld_accesslog.objects.filter(q).values('action').annotate(
                    Count('action'))
                print('count_action_data -->', objs)

                detail_dict = {}
                for obj in objs:
                    print('---------->>', obj['action'], obj['action__count'])
                    detail_dict[obj.get('action')] = obj['action__count']

                action_dict = {

                    1: '查看名片',
                    2: '查看产品',  # 查看您的产品; 查看竞价排名; 转发了竞价排名。
                    3: '查看动态',  # 查看了公司的动态。 评论了您的企业动态。
                    4: '查看官网',  # 查看了您的官网 , 转发了您官网。
                    5: '复制微信',
                    6: '转发名片',
                    7: '咨询产品',
                    8: '保存电话',
                    9: '觉得靠谱',  # 取消了对您的靠谱
                    10: '拨打电话',
                    11: '播放语音',
                    12: '复制邮箱',
                }

                print('----detail_dict----->>', detail_dict)

                response.code = 200
                response.msg = '查询日志记录成功'
                response.data['action'] = action_dict
                response.data['detail'] = detail_dict
                response.data['user_id'] = user_id

                return JsonResponse(response.__dict__)

        elif oper_type == 'customer':
            forms_obj = ActionCustomerForm(request.GET)
            if forms_obj.is_valid():
                response = Response.ResponseObj()

                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']

                field_dict = {
                    'id': '',
                    'user_id': '',
                    'name': '__contains',
                    'create_date__gte': '',
                }

                q = conditionCom(request, field_dict)

                create_date__gte = request.GET.get('create_date__gte')
                create_date__lt = request.GET.get('create_date__lt')
                if not create_date__gte:
                    now_time = datetime.now()
                    create_date__gte = (now_time - timedelta(days=7)).strftime("%Y-%m-%d")
                    q.add(Q(**{'create_date__gte': create_date__gte}), Q.AND)

                if create_date__lt:
                    stop_time = (datetime.strptime(create_date__lt, '%Y-%m-%d') + timedelta(days=1)).strftime(
                        "%Y-%m-%d")
                    q.add(Q(**{'create_date__lt': stop_time}), Q.AND)

                objs = models.zgld_accesslog.objects.filter(q).values('customer__headimgurl', 'customer_id',
                                                                      'customer__username').annotate(Count('action'))
                print('customer_action_data -->', objs)

                if length != 0:
                    start_line = (current_page - 1) * length
                    stop_line = start_line + length
                    objs = objs[start_line: stop_line]

                ret_list = []
                for obj in objs:
                    customer_id = obj['customer_id']
                    action_count = obj['action__count']
                    customer_username = obj['customer__username']
                    headimgurl = obj['customer__headimgurl']

                    insert_data = {
                        'customer_id': customer_id,
                        'action_count': action_count,
                        'customer_username': customer_username,
                        'headimgurl': headimgurl
                    }
                    if not ret_list:  # 首次添加
                        ret_list.append(insert_data)

                    else:  # ret_list 中有数据
                        for index, data in enumerate(ret_list):
                            if data['action_count'] < action_count:
                                ret_list.insert(index, insert_data)
                                break
                        else:
                            ret_list.append(insert_data)

                print('ret_list -->', ret_list)

                # action_dict = {}
                # for i in models.zgld_accesslog.action_choices:
                #     action_dict[i[0]] = i[1]
                #
                # customer_id_list = []
                # customer_username = ''
                # customer__headimgurl = ''
                # detail_list = []
                # customer_id = ''
                # total_num = 0
                #
                # temp_dict = {}
                # for obj in objs:
                #     print('obj -->', obj)
                #     customer_id = obj['customer_id']
                #     action_count = obj['action__count']
                #     customer_username = obj['customer__username']
                #     headimgurl = obj['customer__headimgurl']
                #     action = obj['action']
                #     if customer_id in temp_dict:
                #         temp_dict[customer_id]['totalCount'] += action_count
                #         temp_dict[customer_id]['detail'].append({
                #             "count": action_count,
                #             "name": action_dict[action],
                #             "action": action,
                #         })
                #     else:
                #         temp_dict[customer_id] = {
                #             "totalCount": action_count,
                #             "customer_id": customer_id,
                #             "customer_username": customer_username,
                #             "user_id": user_id,
                #             "headimgurl": headimgurl,
                #             "detail": [
                #                 {
                #                     "count": action_count,
                #                     "name": action_dict[action],
                #                     "action": action,
                #
                #                 }
                #             ]
                #         }

                # for obj in objs:
                #     print('---------->>', obj['action'], obj['action__count'])
                #     customer_id_list.append(obj['customer_id'])
                #
                # ids = list(set(customer_id_list))
                # print('------>>',ids)
                # for c_id in  ids:
                #     for obj in objs:
                #
                #         if obj['customer_id'] == c_id:
                #             total_num  += obj['action__count']
                #             customer_id = c_id
                #             customer_username = obj['customer__username']
                #             customer__headimgurl = obj['customer__headimgurl']
                #             detail_list.append({
                #                 'count': obj['action__count'],
                #                 'name': action_dict[obj['action']],
                #                 'action': obj['action']
                #             })
                #
                #     ret_data.append({
                #                 'totalCount': total_num,
                #                 'customer_id': customer_id,
                #                 'customer__username': customer_username ,
                #                 'user_id': user_id,
                #                 'headimgurl': customer__headimgurl,
                #                 'detail': detail_list
                #     })

                # total_num = 0

                response.code = 200
                response.msg = '查询日志记录成功'
                response.data = ret_list

                return JsonResponse(response.__dict__)

        elif oper_type == 'customer_detail':
            response = Response.ResponseObj()
            field_dict = {
                'customer_id': '',
                'user_id': '',
            }

            import json
            q = conditionCom(request, field_dict)
            objs = models.zgld_accesslog.objects.filter(q).values('customer_id', 'action').annotate(Count('action'))
            print('-------objs---->>', json.dumps(list(objs)))

            ret_data = []
            action_dict = {}
            for i in models.zgld_accesslog.action_choices:
                action_dict[i[0]] = i[1]

            temp_dict = {}
            ret_list = []

            temp_dict = {}
            for obj in objs:
                print('obj -->', obj)
                customer_id = obj['customer_id']
                action_count = obj['action__count']

                action = obj['action']
                if customer_id in temp_dict:
                    temp_dict[customer_id]['totalCount'] += action_count
                    temp_dict[customer_id]['detail'].append({
                        "count": action_count,
                        "name": action_dict[action],
                        "action": action,
                    })
                else:
                    temp_dict[customer_id] = {
                        "totalCount": action_count,
                        "customer_id": customer_id,
                        "detail": [
                            {
                                "count": action_count,
                                "name": action_dict[action],
                                "action": action,

                            }
                        ]
                    }
                # ret_list.append(temp_dict)
                # temp_dict = {}

            ret_data.append(temp_dict)

            response.code = 200
            response.msg = '查询日志记录成功'
            response.data = ret_data

            return JsonResponse(response.__dict__)
