from django.shortcuts import render
from wendaku import models
from publickFunc import Response
from publickFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import time
import datetime
import json
from publickFunc.condition_com import conditionCom
from wendaku.forms.keshi_verify import KeshiAddForm, KeshiUpdateForm, KeshiSelectForm


@csrf_exempt
@account.is_token(models.UserProfile)
def keshi(request):
    response = Response.ResponseObj()
    if request.method == "GET":
        forms_obj = KeshiSelectForm(request.GET)
        if forms_obj.is_valid():
            current_page = forms_obj.cleaned_data['current_page']
            length = forms_obj.cleaned_data['length']
            order = request.GET.get('order', '-create_date')

            field_dict = {
                'id': '',
                'name': '__contains',
                'create_date': '',
                'pid_id': '',
                'oper_user__username': '',
            }
            q = conditionCom(request, field_dict)
            print('q -->', q)

            ret_data = []
            objs = models.Keshi.objects.select_related('pid', 'oper_user').filter(q).order_by(order)
            count = objs.count()

            if length != 0:
                start_line = (current_page - 1) * length
                stop_line = start_line + length
                objs = objs[start_line: stop_line]

            for obj in objs:

                if obj.pid:
                    pid__name = obj.pid.name
                    pid_id = obj.pid.id
                else:
                    pid__name = ""
                    pid_id = ""

                ret_data.append({
                    'id': obj.id,
                    'name': obj.name,
                    'create_date': obj.create_date,
                    'pid__name': pid__name,
                    'pid_id': pid_id,
                    'oper_user__username': obj.oper_user.username,
                })
            print('ret_data -->', ret_data)
            response.code = 200
            response.data = {
                'ret_data': list(ret_data),
                'data_count': count
            }
    else:
        response.code = 402
        response.msg = "请求异常"
    return JsonResponse(response.__dict__)


@csrf_exempt
@account.is_token(models.UserProfile)
def keshi_role_oper(request, oper_type, o_id):
    response = Response.ResponseObj()
    oper_user_id = request.GET.get('user_id')
    pid_id = request.POST.get('pid_id')
    name = request.POST.get('name')

    if request.method == "POST":
        if oper_type == "add":
            form_data = {
                'oper_user_id': oper_user_id,
                'pid_id': pid_id,
                'name': name,
            }
            forms_obj = KeshiAddForm(form_data)
            if forms_obj.is_valid():
                # models.Keshi.objects.create(name=name,oper_user_id=user_id,pid_id=user_id)

                # print("forms_obj.cleaned_data --> ", forms_obj.cleaned_data)
                models.Keshi.objects.create(**forms_obj.cleaned_data)

                response.code = 200
                response.msg = "添加成功"
            else:
                response.code = 300
                response.msg = json.loads(forms_obj.errors.as_json())

        elif oper_type == "delete":
            role_objs = models.Keshi.objects.filter(id=o_id)
            if role_objs:
                role_objs.delete()
                response.code = 200
                response.msg = "删除成功"
            else:
                response.code = 302
                response.msg = '用户ID不存在'

        elif oper_type == "update":
            role_update = models.Keshi.objects.filter(id=o_id)
            if role_update:
                form_data = {
                    'user_id': o_id,
                    'name': request.POST.get('name'),
                    'oper_user_id': request.GET.get('user_id'),
                    'pid_id': request.POST.get('pid_id')
                }
                forms_obj = KeshiUpdateForm(form_data)
                if forms_obj.is_valid():
                    user_id = forms_obj.cleaned_data['user_id']
                    name = forms_obj.cleaned_data['name']
                    oper_user_id = forms_obj.cleaned_data['oper_user_id']
                    #  查询数据库  用户id
                    user_objs = models.Keshi.objects.filter(
                        id=user_id
                    )
                    if user_objs:
                        user_objs.update(
                            name=name, oper_user_id=oper_user_id
                        )
                        response.code = 200
                        response.msg = "修改成功"
                    else:
                        response.code = 303
                        response.msg = json.loads(forms_obj.errors.as_json())
                        print(response.msg)
        else:
            response.code = 402
            response.msg = "请求异常"

        return JsonResponse(response.__dict__)
