
from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.role_verify import RoleAddForm, RoleUpdateForm, RoleSelectForm

import json

from publicFunc.condition_com import conditionCom

@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def role(request):
    response = Response.ResponseObj()
    if request.method == "GET":
        # 获取参数 页数 默认1
        forms_obj = RoleSelectForm(request.GET)
        if forms_obj.is_valid():
            print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)

            current_page = forms_obj.cleaned_data['current_page']
            length = forms_obj.cleaned_data['length']
            order = request.GET.get('order', '-create_date')

            field_dict = {
                'id': '',
                'name': '__contains',
                'create_date': '',

            }
            q = conditionCom(request, field_dict)
            print('q -->', q)

            objs = models.zgld_role.objects.filter(q).order_by(order)
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
                    'role_id': obj.id,
                    'create_date': obj.create_date,

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
@account.is_token(models.zgld_admin_userprofile)
def role_oper(request, oper_type, o_id):
    response = Response.ResponseObj()

    if request.method == "POST":
        # 添加角色
        if oper_type == "add":
            role_data = {
                'name' : request.POST.get('name'),

            }
            forms_obj = RoleAddForm(role_data)
            if forms_obj.is_valid():
                models.zgld_role.objects.create(**forms_obj.cleaned_data)
                response.code = 200
                response.msg = "添加成功"
            else:
                # print("验证不通过")
                print(forms_obj.errors)
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 删除该角色
        elif oper_type == "delete":
            print('------delete o_id --------->>',o_id)

            # role_relate_user = models.zgld_role.objects.get(id=o_id).zgld_userprofile_set.all()

            role_objs = models.zgld_role.objects.filter(id=o_id)
            if role_objs:
                role_obj = role_objs[0]
                if role_obj.zgld_admin_userprofile_set.count() == 0:
                    role_objs.delete()
                    response.code = 200
                    response.msg = "删除成功"
                else:
                    response.code = 303
                    response.msg = "该角色下存在用户,请转移用户后再试"
            else:
                response.code = 302
                response.msg = '角色ID不存在'

        # 修改角色
        elif oper_type == "update":
            form_data = {
                'role_id': o_id,
                'name': request.POST.get('name'),

            }
            print(form_data)
            forms_obj = RoleUpdateForm(form_data)
            if forms_obj.is_valid():
                name = forms_obj.cleaned_data['name']
                role_id = forms_obj.cleaned_data['role_id']
                print(role_id)
                role_objs = models.zgld_role.objects.filter(
                    id=role_id
                )
                if role_objs:
                    role_objs.update(
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
