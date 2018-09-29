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
    response = Response.ResponseObj()
    u_id = request.GET.get('user_id')
    u_idObjs = models.zgld_admin_userprofile.objects.filter(id=u_id)
    xiaochengxu = models.zgld_xiaochengxu_app.objects.filter(id=u_idObjs[0].company_id)
    if xiaochengxu:
        userObjs = models.zgld_shangcheng_jichushezhi.objects.filter(xiaochengxuApp_id=xiaochengxu[0].id)
        otherData = []
        for obj in userObjs:
            lunbotu = ''
            if obj.lunbotu:
                lunbotu = json.loads(obj.lunbotu)
            otherData.append({
                'shangChengName': obj.shangChengName,
                'shangHuHao': obj.shangHuHao,
                'shangHuMiYao': obj.shangHuMiYao,
                'lunbotu': lunbotu,
                'yongjin': obj.yongjin,
                'xiaochengxuApp': obj.xiaochengxuApp.name,
                'xiaochengxuApp_id': obj.xiaochengxuApp_id,
                'xiaochengxucompany_id': obj.xiaochengxucompany_id,
                'xiaochengxucompany': obj.xiaochengxucompany.name,
                'zhengshu': obj.zhengshu,
            })
            response.code = 200
            response.msg = '查询成功'
            response.data = {'otherData':otherData}
    else:
        response.code = 301
        response.msg = '您未注册公司, 请联系管理员！'
        response.data = ''
    return JsonResponse(response.__dict__)


# 商城设置
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
