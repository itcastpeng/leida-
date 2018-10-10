import random
import hashlib
import requests
import xml.dom.minidom as xmldom
import qrcode
import uuid, time, json
from zhugeleida import models
from publicFunc import Response
from publicFunc import account
from django.http import JsonResponse
import requests, base64, datetime
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from zhugeleida.views_dir.xiaochengxu import prepaidManagement


response = Response.ResponseObj()
yuzhifu = prepaidManagement
# SHANGHUKEY = ''
# @csrf_exempt
# def payback(request):
#     resultBody = request.body
#     DOMTree = xmldom.parseString(resultBody)
#     collection = DOMTree.documentElement
#     mch_id = collection.getElementsByTagName("mch_id")[0].childNodes[0].data            # 商户号
#     return_code = collection.getElementsByTagName("return_code")[0].childNodes[0].data  # 状态
#     appid = collection.getElementsByTagName("appid")[0].childNodes[0].data              # 小程序appid
#     openid = collection.getElementsByTagName("openid")[0].childNodes[0].data            # 用户openid
#     cash_fee = collection.getElementsByTagName("cash_fee")[0].childNodes[0].data        # 钱数
#     out_trade_no = collection.getElementsByTagName("out_trade_no")[0].childNodes[0].data# 订单号
#     dingDanobjs = models.zgld_shangcheng_dingdan_guanli.objects.filter(orderNumber=out_trade_no)
#     nowDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     if return_code == 'SUCCESS':
#         if dingDanobjs:
#             # 二次 查询是否付款成功
#             result_data = {
#                 'appid': appid,                 # appid
#                 'mch_id': mch_id,               # 商户号
#                 'out_trade_no': out_trade_no,   # 订单号
#                 'nonce_str': generateRandomStamping(),  # 32位随机值
#             }
#             url = 'https://api.mch.weixin.qq.com/pay/orderquery'
#             global SHANGHUKEY
#             SHANGHUKEY = 'dNe089PsAVjQZPEL7ciETtj0DNX5W2RA'  # 商户秘钥KEY
#             stringSignTemp = shengchengsign(result_data, SHANGHUKEY)
#             result_data['sign'] = md5(stringSignTemp).upper()
#             xml_data = toXml(result_data)
#             ret = requests.post(url, data=xml_data, headers={'Content-Type': 'text/xml'})
#             ret.encoding = 'utf8'
#             DOMTree = xmldom.parseString(ret.text)
#             collection = DOMTree.documentElement
#             return_code = collection.getElementsByTagName("return_code")[0].childNodes[0].data
#             if return_code == 'SUCCESS':
#                 dingDanobjs.update(
#                     theOrderStatus=8,        # 支付成功 改订单状态成功
#                     stopDateTime=nowDate
#                 )
#             else:
#                 dingDanobjs.update(
#                     theOrderStatus=9,  # 支付失败 改订单状态失败
#                     stopDateTime = nowDate
#                 )
#     else:
#         dingDanobjs.update(
#             theOrderStatus=9,  # 支付失败 改订单状态失败
#             stopDateTime=nowDate
#         )
#     response.code = 200
#     response.data = ''
#     response.msg = ''
#     return JsonResponse(response.__dict__)




# 关注发放红包(实时发送)
@csrf_exempt
# @account.is_token(models.zgld_customer)
def focusOnIssuedRedEnvelope(request):
    if request.method == 'POST':
        # 获取IP
        print(request.META)
        # if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        #     ip = request.META['HTTP_X_FORWARDED_FOR']
        # else:
        #     ip = request.META['REMOTE_ADDR']
        # url =  'https://api.mch.weixin.qq.com/pay/unifiedorder'  # 微信支付接口

        return JsonResponse(response.__dict__)

        # 无订单情况 必传 4个参数
        # goodsNum = request.POST.get('goodsNum', 1)               # 商品数量
        # goodsId = request.POST.get('goodsId')                 # 商品ID
        # user_id = request.GET.get('user_id')
        # u_id = request.POST.get('u_id')
        # # 传 订单 ID
        # fukuan = request.POST.get('fukuan')                 # 订单已存在 原有订单
        # print('fukuan===============> ',fukuan)
        #
        # userObjs = models.zgld_customer.objects.filter(id=user_id)  # 客户
        # openid = userObjs[0].openid                                 # openid  用户标识
        # if not fukuan :
        #     u_idObjs = models.zgld_userprofile.objects.filter(id=u_id)
        #     xiaochengxu_app = models.zgld_xiaochengxu_app.objects.filter(company_id=u_idObjs[0].company_id)  # 真实数据appid
        #     goodsObjs = models.zgld_goods_management.objects.filter(id=goodsId)  # 真实单价
        #     jiChuSheZhiObjs = models.zgld_shangcheng_jichushezhi.objects.filter(xiaochengxuApp_id=xiaochengxu_app[0].id)
        #     # ==========商户KEY============
        #     global SHANGHUKEY
        #     SHANGHUKEY = 'dNe089PsAVjQZPEL7ciETtj0DNX5W2RA'            # 商户秘钥KEY
        #     # SHANGHUKEY = jiChuSheZhiObjs[0].shangHuMiYao             # 商户秘钥真实数据KEY
        #     total_fee = int(goodsObjs[0].goodsPrice * 100) * int(goodsNum)
        #     # total_fee = int(0.01 * 100)
        #     ymdhms = time.strftime("%Y%m%d%H%M%S", time.localtime()) # 年月日时分秒
        #     shijianchuoafter5 = str(int(time.time() * 1000))[8:] # 时间戳 后五位
        #     dingdanhao = str(ymdhms) + shijianchuoafter5 + str(random.randint(10, 99)) + str(goodsId)
        #     getWxPayOrderId =  dingdanhao                               # 订单号
        #     appid = xiaochengxu_app[0].authorization_appid              # 预支付 appid
        #     mch_id = jiChuSheZhiObjs[0].shangHuHao
        # # 存在订单的
        # else:
        #     orderObjs = models.zgld_shangcheng_dingdan_guanli.objects.filter(id=fukuan)
        #     getWxPayOrderId = orderObjs[0].orderNumber  #订单号
        #     goodNum = 1
        #     if orderObjs[0].unitRiceNum:
        #         goodNum = orderObjs[0].unitRiceNum
        #
        #     total_fee = int(orderObjs[0].yingFuKuan * 100) * int(goodNum)
        #
        # # client_ip = ip   # 用户ip
        # client_ip = '0.0.0.0'
        # result_data = {
        #     'appid': 'wx1add8692a23b5976',                  # appid
        #     # 'appid': appid,                               # 真实数据appid
        #     'mch_id': '1513325051',                         # 商户号
        #     # 'mch_id': mch_id,                             # 商户号真实数据
        #     'nonce_str': yuzhifu.generateRandomStamping(),          # 32位随机值a
        #     'openid': openid,
        #     'body': 'zhuge-vip',                            # 描述
        #     'out_trade_no': getWxPayOrderId,                # 订单号
        #     'total_fee': total_fee,                            # 金额
        #     'spbill_create_ip': client_ip,                   # 终端IP
        #     'notify_url': 'http://api.zhugeyingxiao.com/zhugeleida/xiaochengxu/payback',
        #     'trade_type': 'JSAPI'
        #     }
        # stringSignTemp = yuzhifu.shengchengsign(result_data, SHANGHUKEY)
        # result_data['sign'] = yuzhifu.md5(stringSignTemp).upper()
        # xml_data = yuzhifu.toXml(result_data)
        # print('xml_data----------------> ',xml_data)
        #
        # ret = requests.post(url, data=xml_data, headers={'Content-Type': 'text/xml'})
        # ret.encoding = 'utf8'
        # print('ret.text============> ',ret.text)
        # DOMTree = xmldom.parseString(ret.text)
        # collection = DOMTree.documentElement
        # return_code = collection.getElementsByTagName("return_code")[0].childNodes[0].data
        # print('return_code-------------------> ',return_code)
        # if return_code == 'SUCCESS':        # 判断预支付返回参数 是否正确
        #     # code_url = collection.getElementsByTagName("code_url")[0].childNodes[0].data  # 二维码
        #     prepay_id = collection.getElementsByTagName("prepay_id")[0].childNodes[0].data  # 直接支付
        #     data_dict = {
        #         'appId' : 'wx1add8692a23b5976',
        #         'timeStamp': int(time.time()),
        #         'nonceStr':yuzhifu.generateRandomStamping(),
        #         'package': 'prepay_id=' + prepay_id,
        #         'signType': 'MD5'
        #     }
        #     stringSignTemp = yuzhifu.shengchengsign(data_dict, SHANGHUKEY)
        #     data_dict['paySign'] = yuzhifu.md5(stringSignTemp).upper() # upper转换为大写
        #     response.code = 200
        #     response.msg = '支付成功'
        #     # 预支付成功 创建订单
        #     if not fukuan:
        #         dingDanObjs = models.zgld_shangcheng_dingdan_guanli.objects
        #         date_time = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        #         commissionFee = 0
        #         if goodsObjs[0].commissionFee:
        #             commissionFee = goodsObjs[0].commissionFee
        #         company_id = xiaochengxu_app[0].company_id
        #         dingDanObjs.create(
        #             shangpinguanli_id = goodsId,            # 商品ID
        #             orderNumber = int(getWxPayOrderId),     # 订单号
        #             yingFuKuan = float(total_fee)/100,             # 应付款
        #             goodsPrice = goodsObjs[0].goodsPrice,   # 商品单价
        #             youHui = 0,                             # 优惠
        #             unitRiceNum=int(goodsNum),                   # 数量
        #             yewuUser_id = u_id,                     # 业务
        #             gongsimingcheng_id = company_id,        # 公司
        #             yongJin = commissionFee,                # 佣金
        #             peiSong = '',                           # 配送
        #             shouHuoRen_id = user_id,                   # 收货人
        #             theOrderStatus = 1,                     # 订单状态
        #             createDate=date_time,
        #             goodsName=goodsObjs[0].goodsName,
        #             detailePicture=goodsObjs[0].detailePicture
        #         )

                # dingdanId = dingdan.id
                # bumen = u_idObjs[0].department.get()
                # phone = int(u_idObjs[0].wechat_phone)
                # models.zgld_yuangong_dingdan_tongji.objects.create(
                #     dingDanguanli_id=dingdanId,
                #     bumen=bumen.name,
                #     touxiang=u_idObjs[0].avatar,
                #     gongsimingcheng_id=u_idObjs[0].company_id,
                #     employeesName_id=u_id,
                #     employeesPhone=phone
                #     # numberOfSalesOrders
                #     # ClinchADealAmount
                # )
            #     response.code = 200
            #     response.msg = '预支付请求成功'
            #     response.data = data_dict
            # return JsonResponse(response.__dict__)
    #     else:
    #         if not fukuan:
    #             response.msg = '预支付失败'
    #         else:
    #             response.msg = '支付失败'
    #         response.code = 500
    #         response.data = ''
    #         return JsonResponse(response.__dict__)
    # else:
    #     response.code = 402
    #     response.msg = '请求异常'
    #     response.data = ''
    #     return JsonResponse(response.__dict__)