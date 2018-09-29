from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.admin.shangchengshezhi_verify import jichushezhi, zhifupeizhi, yongjinshezhi
import json

@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def jiChuSheZhiShow(request):
    u_id = request.GET.get('user_id')
    u_idObjs = models.zgld_admin_userprofile.objects.filter(id=u_id)
    xiaochengxu = models.zgld_xiaochengxu_app.objects.filter(id=u_idObjs[0].company_id)
    if xiaochengxu:
        userObjs = models.zgld_shangcheng_jichushezhi.objects.filter(xiaochengxuApp_id=xiaochengxu[0].id)
        if userObjs:
            pass
        else:
            print('基础设置为空')
    else:
        print('没有小程序')





@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def jiChuSheZhiOper(request, oper_type):
    response = Response.ResponseObj()
    if request.method == "POST":
        user_id = request.GET.get('user_id')
        u_idObjs = models.zgld_admin_userprofile.objects.filter(id=user_id)
        xiaochengxu = models.zgld_xiaochengxu_app.objects.filter(id=u_idObjs[0].company_id)
        userObjs = models.zgld_shangcheng_jichushezhi.objects.filter(xiaochengxuApp_id=xiaochengxu[0].id)
        if oper_type == 'jichushezhi':
            resultData = {
                'shangChengName' : request.POST.get('shangChengName'),
                'lunbotu' : request.POST.get('lunbotu'),
            }
            forms_obj = jichushezhi(resultData)
            if forms_obj.is_valid():
                formObjs = forms_obj.cleaned_data
                print('验证通过')
                if userObjs:
                    userObjs.update(
                        shangChengName=formObjs.get('shangChengName'),
                        lunbotu=formObjs.get('lunbotu'),
                    )
                    response.msg = '修改成功'
                else:
                    models.zgld_shangcheng_jichushezhi.objects.create(
                        shangChengName=formObjs.get('shangChengName'),
                        lunbotu=formObjs.get('lunbotu'),
                    )
                    response.msg = '创建成功'
                response.code = 200
                response.data = ''
            else:
                response.code = 301
                response.data = json.loads(forms_obj.errors.as_json())
        if oper_type == 'zhifupeizhi':
            print('==================')
            resultData = {
                'shangHuHao': request.POST.get('shangHuHao'),
                'shangHuMiYao': request.POST.get('shangHuMiYao'),
                'zhengshu': request.POST.get('zhengshu'),
            }
            forms_obj = zhifupeizhi(resultData)
            if forms_obj.is_valid():
                print('支付配置 验证成功')
                formObjs = forms_obj.cleaned_data
                if userObjs:
                    userObjs.update(
                        shangHuHao=formObjs.get('shangHuHao'),
                        shangHuMiYao=formObjs.get('shangHuMiYao'),
                        zhengshu=formObjs.get('zhengshu')
                    )
                    response.msg = '修改成功'
                else:
                    models.zgld_shangcheng_jichushezhi.objects.create(
                        shangHuHao=formObjs.get('shangHuHao'),
                        shangHuMiYao=formObjs.get('shangHuMiYao'),
                        zhengshu=formObjs.get('zhengshu')
                    )
                    response.msg = '创建成功'
                response.code = 200
                response.data = ''
            else:
                response.code = 301
                response.data = json.loads(forms_obj.errors.as_json())

        if oper_type == 'yongjinshezhi':
            resultData = {
                'yongjin': request.POST.get('yongjin'),
            }
            forms_obj = yongjinshezhi(resultData)
            if forms_obj.is_valid():
                formObjs = forms_obj.cleaned_data
                if userObjs:
                    userObjs.update(
                        yongjin=formObjs.get('yongjin')
                    )
                    response.msg = '修改成功'
                else:
                    models.zgld_shangcheng_jichushezhi.objects.create(
                        yongjin=formObjs.get('yongjin'),
                    )
                response.code = 200
                response.data = ''
            else:
                response.code = 301
                response.data = json.loads(forms_obj.errors.as_json())
    else:
        response.code = 402
        response.msg = "请求异常"

    return JsonResponse(response.__dict__)
