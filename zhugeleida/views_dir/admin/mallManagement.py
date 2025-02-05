from django.shortcuts import render
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.forms.xiaochengxu.mallManage_verify import AddForm, UpdateForm, SelectForm
import json,os,sys
from django.db.models import Q
import datetime

# 方便查询调用  封装接口
def mallManagementshow(request, user_id, goodsGroup, status, flag):
    response = Response.ResponseObj()
    if request.method == "GET":
        forms_obj = SelectForm(request.GET)
        if forms_obj.is_valid():
            id = request.GET.get('id')
            company_id = request.GET.get('company_id')
            order = request.GET.get('order','-recommend_index')

            current_page = forms_obj.cleaned_data['current_page']
            length = forms_obj.cleaned_data['length']
            q = Q()
            print('goodsGroup--> ',goodsGroup, 'status---> ',status)
            if goodsGroup:
                q.add(Q(parentName_id=goodsGroup), Q.AND)
            if status:
                q.add(Q(goodsStatus=status), Q.AND)
            if id:
                q.add(Q(id=id), Q.AND)

            if flag != 'admin':
                u_idObjs = models.zgld_customer.objects.get(id=user_id)
                company_id  = u_idObjs.company_id

            objs = models.zgld_goods_management.objects.filter(q).filter(company_id=company_id).order_by(order)

            objsCount = objs.count()
            otherData = []
            if length != 0:
                start_line = (current_page - 1) * length
                stop_line = start_line + length
                objs = objs[start_line: stop_line]

            for obj in objs:
                groupObjs = models.zgld_goods_classification_management.objects.filter(id=obj.parentName_id)
                parentGroup_id = obj.parentName_id
                parentGroup_name = obj.parentName.classificationName
                if groupObjs[0].parentClassification_id:
                    parent_group_name = groupObjs[0].parentClassification.classificationName
                    parentGroup_name = parent_group_name + ' > ' + parentGroup_name

                xianshangjiaoyi = '否'
                if obj.xianshangjiaoyi:
                    xianshangjiaoyi = '是'
                topLunBoTu = ''
                if obj.topLunBoTu:
                    topLunBoTu = json.loads(obj.topLunBoTu)

                content = ''
                if obj.content:
                    content = json.loads(obj.content)

                shelvesCreateDate = ''
                if obj.shelvesCreateDate:
                    shelvesCreateDate = obj.shelvesCreateDate.strftime('%Y-%m-%d %H:%M:%S')
                otherData.append({
                    'id':obj.id,
                    'goodsName':obj.goodsName,
                    'parentName_id':parentGroup_id,
                    'parentName':parentGroup_name,
                    'goodsPrice':obj.goodsPrice,
                    # 'inventoryNum':obj.inventoryNum,
                    'goodsStatus_code':obj.goodsStatus,
                    'goodsStatus':obj.get_goodsStatus_display(),
                    'xianshangjiaoyi':xianshangjiaoyi,
                    'shichangjiage':obj.shichangjiage,
                    # 'kucunbianhao':obj.kucunbianhao,
                    'topLunBoTu': topLunBoTu,  # 顶部轮播图
                    # 'detailePicture' : detailePicture,  # 详情图片
                    'content' : content,  # 详情图片
                    'recommend_index' : obj.recommend_index,  # 详情图片
                    'createDate': obj.createDate.strftime('%Y-%m-%d %H:%M:%S'),
                    'shelvesCreateDate':shelvesCreateDate,
                    'DetailsDescription': obj.DetailsDescription # 描述详情
                })

            response.code = 200
            response.msg = '查询成功'
            response.data = {
                'otherData':otherData,
                'objsCount':objsCount
            }

    return response

# 查询该商品 所有父级分组
def updateInitData(result_data,xiaochengxu_id, pid=None):   # 更新查询 分类接口
    objs = models.zgld_goods_classification_management.objects.filter(
        mallSetting_id=xiaochengxu_id,
        id=pid,
    )
    for obj in objs:
        parent = updateInitData(result_data, xiaochengxu_id, pid=obj.parentClassification_id)
        result_data.append(obj.id)

    return result_data


# 商城商品查询
@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def mallManagement(request):
    user_id = request.GET.get('user_id')
    goodsGroup = request.GET.get('goodsGroup')
    status = request.GET.get('status')
    flag = 'admin'
    response = mallManagementshow(request, user_id, goodsGroup, status, flag)
    return JsonResponse(response.__dict__)


# 商城商品操作
@csrf_exempt
@account.is_token(models.zgld_admin_userprofile)
def mallManagementOper(request, oper_type, o_id):
    response = Response.ResponseObj()
    resultData = {
        'user_id':request.GET.get('user_id'),
        'o_id':o_id,
        'goodsName':request.POST.get('goodsName'),                    # 商品名称
        'parentName':request.POST.get('parentName'),                  # 父级分类
        'goodsPrice':request.POST.get('goodsPrice'),                  # 商品标价
        # 'inventoryNum':request.POST.get('inventoryNum'),            # 商品库存
        'goodsStatus':request.POST.get('goodsStatus'),                # 商品状态
        'xianshangjiaoyi':request.POST.get('xianshangjiaoyi'),        # 是否线上交易
        'shichangjiage':request.POST.get('shichangjiage'),            # 市场价格
        # 'kucunbianhao':request.POST.get('kucunbianhao'),            # 库存编号
        'topLunBoTu':request.POST.get('topLunBoTu'),                  # 顶部轮播图
        # 'detailePicture':request.POST.get('detailePicture'),          # 详情图片
        'DetailsDescription': request.POST.get('DetailsDescription'),  # 描述详情
        'content': request.POST.get('content')  # 描述详情
    }
    print('resultData---------------->',resultData)
    user_id = request.GET.get('user_id')
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if request.method == "POST":
        # 添加商品
        if oper_type == 'add':
            forms_obj = AddForm(resultData)
            company_id = request.GET.get('company_id')

            if forms_obj.is_valid():
                formObjs = forms_obj.cleaned_data
                print('验证通过')
                print('nowDate-------------> ',nowDate)
                content = forms_obj.cleaned_data.get('content')

                objs = models.zgld_goods_management.objects.create(
                    company_id = company_id,
                    goodsName=formObjs.get('goodsName'),
                    parentName_id=formObjs.get('parentName'),
                    goodsPrice=formObjs.get('goodsPrice'),
                    # inventoryNum=formObjs.get('inventoryNum'),
                    xianshangjiaoyi=formObjs.get('xianshangjiaoyi'),
                    shichangjiage=formObjs.get('shichangjiage'),
                    # kucunbianhao=formObjs.get('kucunbianhao'),
                    goodsStatus=formObjs.get('goodsStatus'),
                    topLunBoTu=resultData.get('topLunBoTu'),  # 顶部轮播图

                    # detailePicture=resultData.get('detailePicture'),  # 详情图片
                    content=content,
                    DetailsDescription=formObjs.get('DetailsDescription') # 描述详情
                )
                if formObjs.get('goodsStatus') == 1:
                    models.zgld_goods_management.objects.filter(id=objs.id).update(
                        shelvesCreateDate=nowDate
                    )
                response.code = 200
                response.msg = '添加成功'

            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 查询该商品 分组信息
        elif oper_type == 'Beforeupdate':
            goodsObjs = models.zgld_goods_management.objects.get(id=o_id) # 商品ID
            u_idObjs = models.zgld_admin_userprofile.objects.get(id=user_id)
            userObjs = models.zgld_shangcheng_jichushezhi.objects.filter(xiaochengxuApp__company_id=u_idObjs.company_id)
            objs = models.zgld_goods_classification_management.objects.filter(id=goodsObjs.parentName_id)
            result_data = []
            parentData = updateInitData(result_data, userObjs[0].id, objs[0].parentClassification_id)
            parentData.append(goodsObjs.parentName_id)  # 添加自己本身分组ID
            response.code = 200
            response.msg = '查询成功'
            response.data = parentData # 根据 分组上下级关系 由大到小列表排列ID

        # 修改商品
        elif oper_type == 'update':
            forms_obj = UpdateForm(resultData)
            if forms_obj.is_valid():
                formObjs = forms_obj.cleaned_data
                content = forms_obj.cleaned_data.get('content')

                objs = models.zgld_goods_management.objects.filter(id=o_id)
                if not objs[0].shelvesCreateDate and formObjs.get('goodsStatus') == 1:# 判断如果原本上架时间为空 且当前传上架时间 则更改
                    objs.update(shelvesCreateDate=nowDate)

                print("formObjs.get('DetailsDescription')============> ",formObjs.get('DetailsDescription'))
                objs.update(
                    goodsName=formObjs.get('goodsName'),
                    parentName_id=formObjs.get('parentName'),
                    goodsPrice=formObjs.get('goodsPrice'),
                    shichangjiage=formObjs.get('shichangjiage'),
                    # kucunbianhao=formObjs.get('kucunbianhao'),
                    goodsStatus=formObjs.get('goodsStatus'),
                    topLunBoTu=resultData.get('topLunBoTu'),            # 顶部轮播图
                    # detailePicture=resultData.get('detailePicture'),    # 详情图片
                    xianshangjiaoyi=formObjs.get('xianshangjiaoyi'),
                    DetailsDescription=formObjs.get('DetailsDescription'),
                    content=content,                  # 描述详情
                )
                response.code = 200
                response.msg = '修改成功'
                response.data = {}
            else:
                response.code = 301
                response.msg = json.loads(forms_obj.errors.as_json())

        # 删除商品
        elif oper_type == 'delete':
            objs = models.zgld_goods_management.objects.filter(id=o_id)
            if objs:
                topLunBoTu = objs[0].topLunBoTu
                dingdan_objs = models.zgld_shangcheng_dingdan_guanli.objects.filter(shangpinguanli_id=o_id)
                if dingdan_objs:
                    dingdan_objs.update(
                        shangpinguanli_id=None,
                        goods_id=o_id,
                        topLunBoTu=topLunBoTu
                    )

                objs.delete()

                response.code = 200
                response.msg = '删除成功'
                response.data = {}
            else:
                response.code = 301
                response.msg = '删除ID不存在！'

    else:
        # 查询商品所有状态
        if oper_type == 'goodsStatus': # 查询商品状态
            objs = models.zgld_goods_management
            otherData = []
            for status in objs.status_choices:
                otherData.append({
                    'id':status[0],
                    'name':status[1]
                })
            response.code = 200
            response.msg = '查询成功'
            response.data = otherData

        else:
            response.code = 402
            response.msg = "请求异常"


    return JsonResponse(response.__dict__)




