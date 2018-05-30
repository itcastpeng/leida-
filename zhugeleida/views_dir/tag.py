
from django.shortcuts import render
from zhugeleida import models
from publickFunc import Response
from publickFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.tag_verify import TagAddForm, TagUpdateForm, TagSelectForm
import time
import datetime
import json

from publickFunc.condition_com import conditionCom

@csrf_exempt
@account.is_token(models.zgld_userprofile)
def tag(request):
    response = Response.ResponseObj()
    if request.method == "GET":
        # 获取参数 页数 默认1
        forms_obj = TagSelectForm(request.GET)
        if forms_obj.is_valid():
            print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)

            current_page = forms_obj.cleaned_data['current_page']
            length = forms_obj.cleaned_data['length']
            order = request.GET.get('order', '-create_date')

            field_dict = {
                'id': '',
                'name': '__contains',
            }
            q = conditionCom(request, field_dict)
            print('q -->', q)

            objs = models.zgld_tag.objects.filter(q).order_by(order)
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

                ret_data.append({
                    'id': obj.id,
                    'name': obj.name,
                    'tag_id': obj.id,
                })
            response.code = 200
            response.data = {
                'ret_data': ret_data,
                'data_count': count,
            }
        return JsonResponse(response.__dict__)

    else:
        response.code = 402
        response.msg = "请求异常"


@csrf_exempt
@account.is_token(models.zgld_userprofile)
def tag_oper(request, oper_type, o_id):
    response = Response.ResponseObj()

    if request.method == "POST":
        if oper_type == "add":
            tag_data = {
                'name' : request.POST.get('name'),
                'oper_user_id':request.GET.get('user_id')
            }
            forms_obj = TagAddForm(tag_data)
            if forms_obj.is_valid():
                models.zgld_tag.objects.create(**forms_obj.cleaned_data)
                response.code = 200
                response.msg = "添加成功"
            else:
                # print("验证不通过")
                print(forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        elif oper_type == "delete":
            print('------delete o_id --------->>',o_id)
            tag_objs = models.zgld_tag.objects.filter(id=o_id)
            if tag_objs:
                tag_objs.delete()
                response.code = 200
                response.msg = "删除成功"
            else:
                response.code = 302
                response.msg = '角色ID不存在'

        elif oper_type == "update":
            form_data = {
                'tag_id': o_id,
                'name': request.POST.get('name'),
                'oper_user_id': request.POST.get('user_id'),
            }
            print(form_data)
            forms_obj = TagUpdateForm(form_data)
            if forms_obj.is_valid():
                name = forms_obj.cleaned_data['name']
                tag_id = forms_obj.cleaned_data['tag_id']
                print(tag_id)
                tag_objs = models.zgld_tag.objects.filter(
                    id=tag_id
                )
                if tag_objs:
                    tag_objs.update(
                        name=name
                    )
                    response.code = 200
                    response.msg = "修改成功"
                else:
                    response.code = 302
                    response.msg = '角色ID不存在'
            else:
                response.code = 303
                response.msg = json.loads(forms_obj.errors.as_json())

    else:
        response.code = 402
        response.msg = "请求异常"

    return JsonResponse(response.__dict__)
