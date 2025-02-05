from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from publicFunc.condition_com import conditionCom
from zhugeleida.forms.admin.product_verify import ProductSelectForm, ProductGetForm,ProductAddForm,imgMergeForm,imgUploadForm,FeedbackSelectForm
from zhugeleida.forms.qiyeweixin.product_verify import  ProductUpdateForm,RecommendIndexForm
import json
from django.db.models import Q
import os
import base64

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BasePath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def sort_article_data(data):
    ret_list = []
    for obj in data:
        if not ret_list:
            # tmp_dict[obj['order']] = obj
            ret_list.append(obj)

        else:
            for index, data in enumerate(ret_list):
                if obj['order'] < data['order']:
                    ret_list.insert(index, obj)
                    break
            else:
                ret_list.append(obj)
    return ret_list


@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def product(request, oper_type):
    response = Response.ResponseObj()

    if request.method == "GET":

        # 官网产品展示
        if oper_type == 'product_single':
            product_type = int(request.GET.get('product_type')) if request.GET.get('product_type') else ''
            user_id = request.GET.get('user_id')
            product_id = request.GET.get('product_id')
            field_dict = {
                'id': '',
            }
            q = conditionCom(request, field_dict)
            q.add(Q(**{'id': product_id}), Q.AND)

            if product_type  == 1:   #单个官网产品展示
                q.add(Q(**{'user_id__isnull': True }), Q.AND)

            elif product_type == 2:
                q.add(Q(**{'user_id__isnull': False }), Q.AND)

            objs = models.zgld_product.objects.select_related('user', 'company').filter(q)
            count = objs.count()

            if objs:
                ret_data = []
                for obj in objs:
                    if obj.user_id:
                        if int(obj.user_id) == int(user_id):
                            publisher = '我添加的'
                        else:
                            publisher = obj.user.username + '添加的'
                    else:
                        publisher = '企业发布'

                    ret_data.append({
                        'id': obj.id,

                        'publisher': publisher,  # 发布者
                        'publisher_date': obj.create_date,  # 发布日期。

                        'name': obj.name,  # 产品名称  必填
                        'price': obj.price,  # 价格     必填
                        'reason': obj.reason,  # 推荐理由
                        'content' : json.loads(obj.content),

                        'create_date': obj.create_date.strftime("%Y-%m-%d"),  # 发布的日期
                        'status': obj.get_status_display(),  # 产品的动态
                        'status_code': obj.status  # 产品的动态值。

                    })
                    #  查询成功 返回200 状态码
                    response.code = 200
                    response.msg = '查询成功'
                    response.data = {
                        'ret_data': ret_data,
                        'data_count': count,
                    }

            else:
                response.code = 302
                response.msg = "产品不存在"

        # 产品详情展示
        elif oper_type == 'product_list':
            print('request.GET----->', request.GET)
            forms_obj = ProductSelectForm(request.GET)
            if forms_obj.is_valid():
                print('----forms_obj.cleaned_data -->', forms_obj.cleaned_data)
                product_type = forms_obj.cleaned_data.get('product_type')

                #如果为1 代表是公司的官网
                user_id = request.GET.get('user_id')
                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-recommend_index')

                q1 = Q()
                q1.connector = 'and'
                user_obj = models.zgld_admin_userprofile.objects.filter(id=user_id)[0]
                company_id = user_obj.company_id

                if product_type == 1:   # 展示公司 产品
                     q1.children.append(('user_id__isnull', True))
                elif product_type == 2: # 展示个人 产品
                     q1.children.append(('user_id__isnull', False))

                q1.children.append(('company_id', company_id))

                search_product_name = request.GET.get('product_name')  # 当有搜索条件 如 搜索产品名称
                if search_product_name:
                    q1.children.append(('name__contains', search_product_name))

                search_product_status = request.GET.get('status')  # 当有搜索条件 如 搜索上架或者不上架的
                if not search_product_status:
                    q1.children.append(('status__in', [1, 3]))  # 默认是显示出所有的上架的产品
                else:
                    if int(search_product_status) == 1:
                        q1.children.append(('status__in', [1, 3]))  # (1,'已上架')

                    elif int(search_product_status) == 2:
                        q1.children.append(('status__in', [2]))  # (2,'已下架')

                print('-----q1---->>',q1)
                objs = models.zgld_product.objects.select_related('user', 'company').filter(q1).order_by(order)
                count = objs.count()

                if length != 0:
                    start_line = (current_page - 1) * length
                    stop_line = start_line + length
                    objs = objs[start_line: stop_line]

                ret_data = []

                if objs:
                    for obj in objs:
                        product_id = obj.id

                        if obj.user_id:
                            publisher = obj.user.username
                        else:
                            publisher = obj.company.name

                        content = {
                           'cover_data': json.loads(obj.content).get('cover_data')

                        }

                        ret_data.append({
                            'product_id': product_id,
                            'content': content,  # 封面地址的URL
                            'name': obj.name,  # 产品名称
                            'price': obj.price,  # 价格
                            'publisher_date': obj.create_date.strftime("%Y-%m-%d %H:%M:%S"),  # 发布日期。
                            'publisher': publisher,  # 发布者
                            'status': obj.get_status_display(),
                            'recommend_index': obj.recommend_index, #产品推荐指数
                            'status_code': obj.status  # 产品的动态。
                        })

                        #  查询成功 返回200 状态码
                        response.code = 200
                        response.msg = '查询成功'
                        response.data = {
                            'ret_data': ret_data,
                            'data_count': count,
                        }
                else:
                    response.code = 302
                    response.msg = '产品列表无数据'

            else:
                response.code = 402
                response.msg = "验证未通过"
                response.data = json.loads(forms_obj.errors.as_json())

        # 为超级管理员 展示出所有公司的产品
        elif oper_type == 'feedback_list':
            user_id = request.GET.get('user_id')

            user_obj = models.zgld_admin_userprofile.objects.get(id=user_id)
            role_id  = user_obj.role_id
            print('-----role id ---->>',role_id)
            forms_obj = FeedbackSelectForm(request.GET)
            if forms_obj.is_valid():
                current_page = forms_obj.cleaned_data['current_page']
                length = forms_obj.cleaned_data['length']
                order = request.GET.get('order', '-create_date')

                if int(role_id) == 1:
                    search_company_id = request.GET.get('company_id')  # 当有搜索条件,如 公司搜索
                    field_dict = {
                        'id': '',
                        'company__name': '__contains',
                        'status': '',

                    }


                    q = conditionCom(request, field_dict)
                    if search_company_id:
                        q.add(Q(**{'user__company_id': search_company_id}), Q.AND)

                    objs = models.zgld_user_feedback.objects.select_related('user').filter(q).order_by(order)
                    count = objs.count()
                    print('-----objs----->>', objs)

                    ret_data = []
                    if length != 0:
                        start_line = (current_page - 1) * length
                        stop_line = start_line + length
                        objs = objs[start_line: stop_line]

                    if objs:
                        for obj in objs:
                            ret_data.append({
                                'id': obj.id,
                                'user_id': obj.user_id,
                                'user_name': obj.user.username,
                                'problem_type': obj.problem_type,
                                'problem_type_text': obj.get_problem_type_display(),
                                'content': json.loads(obj.content),
                                'company_name': obj.user.company.name,
                                'company_id': obj.user.company_id,
                                'status': obj.status,
                                'status_text': obj.get_status_display()
                            })

                        #  查询成功 返回200 状态码
                        response.code = 200
                        response.msg = '查询成功'
                        response.data = {
                            'ret_data': ret_data,
                            'data_count': count,
                        }

                else:
                    response.code = 302
                    response.msg = '列表无数据'

            return JsonResponse(response.__dict__)

    return JsonResponse(response.__dict__)

@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def product_oper(request, oper_type, o_id):
    response = Response.ResponseObj()

    if request.method == "POST":

        # 删除-个人产品
        if oper_type == "delete":
            user_id = request.GET.get('user_id')
            user_obj =  models.zgld_admin_userprofile.objects.filter(id=user_id)
            company_id = user_obj[0].company_id

            ids_list = request.POST.get('ids_list')
            if len(ids_list) > 0:
                ids_list = json.loads(ids_list)
            else:
                ids_list = []
            product_objs = models.zgld_product.objects.filter(id__in=ids_list,company_id=company_id)

            if product_objs:
                product_objs.delete()

                response.code = 200
                response.msg = "删除成功"


            else:
                response.code = 301
                response.msg = '产品不存在'

        # 修改 产品上下架 状态
        elif oper_type == "change_status":

            status = int(request.POST.get('status'))
            user_id = request.GET.get('user_id')
            ids_list = request.POST.get('ids_list')
            if len(ids_list) > 0:
                ids_list = json.loads(ids_list)
            else:
                ids_list = []
            product_objs = models.zgld_product.objects.filter(id__in=ids_list)

            if product_objs:

                product_objs.update(
                    status=status
                )
                response.code = 200
                response.msg = "修改状态成功"
                response.data = {
                    'product_id': product_objs[0].id,
                    'status': product_objs[0].get_status_display(),
                    'status_code': product_objs[0].status
                }

            else:

                response.code = 302
                response.msg = '产品不存在'

        # 修改产品
        elif oper_type == "update":

            form_data = {
                'user_id': request.GET.get('user_id'),
                'product_id': o_id,  # 标题    非必须
                'name': request.POST.get('name'),  # 产品名称 必须
                'price': request.POST.get('price'),  # 价格    非必须
                'reason': request.POST.get('reason'),  # 推荐理由 非必须
                'content': request.POST.get('content'),  # 内容 非必须
            }

            forms_obj = ProductUpdateForm(form_data)
            if forms_obj.is_valid():
                user_id = request.GET.get('user_id')
                product_id = forms_obj.cleaned_data.get('product_id')

                product_obj = models.zgld_product.objects.filter(id=product_id)
                product_obj.update(
                    name=forms_obj.cleaned_data.get('name'),
                    price=forms_obj.cleaned_data.get('price'),
                    reason=forms_obj.cleaned_data.get('reason'),
                    content=forms_obj.cleaned_data.get('content')
                )

                response.code = 200
                response.msg = "添加成功"


            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 添加产品
        elif oper_type == "add":

            form_data = {
                'user_id': request.GET.get('user_id'),
                'name': request.POST.get('name'),  # 产品名称 必须
                'price': request.POST.get('price'),  # 价格     必须
                'reason': request.POST.get('reason'),  # 推荐理由 非必须
                'product_type': request.POST.get('product_type'),    # 标题    非必须
                'content': request.POST.get('content'),  # 内容    非必须
            }
            product_type = int(request.POST.get('product_type')) if request.POST.get('product_type') else ''

            forms_obj = ProductAddForm(form_data)
            if forms_obj.is_valid():
                user_id = request.GET.get('user_id')
                content = forms_obj.cleaned_data.get('content')

                global product_owner
                if product_type == 1:             #代表公司产品
                    product_owner = ''
                elif product_type == 2:           #代表个人产品
                    product_owner = user_id

                company_id = models.zgld_admin_userprofile.objects.get(id=user_id).company_id
                product_obj = models.zgld_product.objects.create(
                    user_id=product_owner,
                    company_id=company_id,
                    name=forms_obj.cleaned_data.get('name'),
                    price=forms_obj.cleaned_data.get('price'),
                    reason=forms_obj.cleaned_data.get('reason'),
                )

                # 封面图片数据绑定到产品。
                product_obj.content = content
                product_obj.save()

                response.code = 200
                response.msg = "添加成功"

            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        ## 修改推荐指数-影响产品展示排序。
        elif oper_type == 'recommend_index':
            type = request.POST.get('type')

            form_data = {
                'user_id': request.GET.get('user_id'),
                'product_id': o_id,  # 产品ID
                'recommend_index' : request.POST.get('recommend_index') # 排序优先级。
            }

            forms_obj = RecommendIndexForm(form_data)
            if forms_obj.is_valid():
                user_id = request.GET.get('user_id')
                product_id = forms_obj.cleaned_data.get('product_id')
                recommend_index = forms_obj.cleaned_data.get('recommend_index')

                if type == 'goods':
                    goods_obj = models.zgld_goods_management.objects.filter(id=product_id)
                    goods_obj.update(
                        recommend_index=recommend_index
                    )

                else:
                    product_obj = models.zgld_product.objects.filter(id=product_id)
                    product_obj.update(
                        recommend_index=recommend_index
                    )

                response.code = 200
                response.msg = "修改成功"
            else:
                response.code = 303
                response.msg = "验证未通过"
                response.data = json.loads(forms_obj.errors.as_json())

        # 上传产品图片的接口
        elif oper_type == "add_picture":
            response = Response.ResponseObj()

            forms_obj = imgUploadForm(request.POST)
            if forms_obj.is_valid():
                img_name = forms_obj.cleaned_data.get('img_name')  # 图片名称
                timestamp = forms_obj.cleaned_data.get('timestamp')  # 时间戳
                img_data = forms_obj.cleaned_data.get('img_data')  # 文件内容
                chunk = forms_obj.cleaned_data.get('chunk')  # 第几片文件
                expanded_name = img_name.split('.')[-1]  # 扩展名

                img_name = timestamp + "_" + str(chunk) + '.' + expanded_name

                img_save_path = "/".join(
                    [BasePath, 'statics', 'zhugeleida', 'imgs', 'qiyeweixin', 'product', 'tmp', img_name])
                print('img_save_path -->', img_save_path)

                img_data = base64.b64decode(img_data.encode('utf-8'))
                with open(img_save_path, 'wb') as f:
                    f.write(img_data)

                response.code = 200
                response.msg = "上传成功"
            else:
                response.code = 303
                response.msg = "上传异常"
                response.data = json.loads(forms_obj.errors.as_json())
            return JsonResponse(response.__dict__)

        # 产品图片合并请求
        elif oper_type == "upload_complete":

            response = Response.ResponseObj()
            forms_obj = imgMergeForm(request.POST)
            if forms_obj.is_valid():
                img_name = forms_obj.cleaned_data.get('img_name')  # 图片名称
                timestamp = forms_obj.cleaned_data.get('timestamp')  # 时间戳
                chunk_num = forms_obj.cleaned_data.get('chunk_num')  # 一共多少份
                expanded_name = img_name.split('.')[-1]  # 扩展名
                picture_type = forms_obj.cleaned_data.get('picture_type')  # 图片的类型  (1, '产品封面的图片'), (2, '产品介绍的图片')

                img_name = timestamp + '.' + expanded_name
                img_path = "/".join(['statics', 'zhugeleida', 'imgs', 'qiyeweixin', 'product', img_name])
                img_save_path = "/".join([BasePath, img_path])
                file_obj = open(img_save_path, 'ab')
                for chunk in range(chunk_num):
                    file_name = timestamp + "_" + str(chunk) + '.' + expanded_name

                    file_save_path = "/".join(
                        [BasePath, 'statics', 'zhugeleida', 'imgs', 'qiyeweixin', 'product', 'tmp', file_name])

                    with open(file_save_path, 'rb') as f:
                        file_obj.write(f.read())

                    os.remove(file_save_path)

                product_picture_obj = models.zgld_product_picture.objects.create(picture_type=picture_type,
                                                                                 picture_url=img_path)

                response.data = {
                    'picture_type': product_picture_obj.picture_type,
                    'picture_id': product_picture_obj.id,
                    'picture_url': product_picture_obj.picture_url,

                }
                response.code = 200
                response.msg = "添加图片成功"

            else:
                response.code = 303
                response.msg = "上传异常"
                response.data = json.loads(forms_obj.errors.as_json())

        # 修改意见反馈表状态
        elif oper_type == "change_feedback_status":
            print('-------change_status------->>', request.POST)
            status = int(request.POST.get('status'))

            feedback_objs = models.zgld_user_feedback.objects.filter(id=o_id)

            if feedback_objs:

                feedback_objs.update(
                    status=status
                )
                response.code = 200
                response.msg = "修改状态成功"

            else:

                response.code = 302
                response.msg = '产品不存在'
    else:
        response.code = 402
        response.msg = '请求异常'

    return JsonResponse(response.__dict__)






