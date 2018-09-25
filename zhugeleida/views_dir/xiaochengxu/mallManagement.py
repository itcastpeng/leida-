import random
import hashlib
import requests
import xml.dom.minidom as xmldom
import qrcode
import uuid, time, json
from publicFunc import Response
from django.http import JsonResponse
# ==========商户KEY============
KEY = 'dNe089PsAVjQZPEL7ciETtj0DNX5W2RA'

response = Response.ResponseObj()
def md5(string):
    m = hashlib.md5()
    m.update(string.encode('utf8'))
    return m.hexdigest()

# 返回 xml
def toXml(params):
    xml = []
    for k in sorted(params.keys()):
        v = params.get(k)
        # if k == 'body':
        #     body = params.get(k)
        #     print('body------> ',type(body))
        #     v = body.decode('utf-8')
        # print('v========> ',v)
        if k == 'detail' and not v.startswith('<![CDATA['):
            v = '<![CDATA[{}]]>'.format(v)

        # if k == 'body':
        #     # v = v.encode('utf8')
        #     v = parse.quote(v)
        xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(xml))

# 返回32为 时间戳
def generateRandomStamping():
    return str(uuid.uuid4()).replace('-', '')

# 生成二维码
# def create_qrcode(url):
#     img = qrcode.make(url)
#     img.get_image().show()
#     img.save('hello.png')

# 生成 签名
def shengchengsign(result_data):
    ret = []
    for k in sorted(result_data.keys()):
        if (k != 'sign') and (k != '') and (result_data[k] is not None):
            ret.append('%s=%s' % (k, result_data[k]))

    stringA = '&'.join(ret)
    stringSignTemp = '{stringA}&key={key}'.format(
        stringA=stringA,
        key=KEY
    )
    return stringSignTemp

def pay(request):
    print('回调=-----> ',request.GET)
    print('回调=-----> ',request.POST)
    response.code = 200
    return JsonResponse(response.__dict__)

def yuZhiFu(request):
    timeStamp = generateRandomStamping()   # 时间戳
    getWxPayOrderId = str(int(time.time())) # 订单号
    amount = request.GET.get('amount')
    spbillIp = request.GET.get('spbillIp')
    goodsIntroduce = request.GET.get('goodsIntroduce')
    url =  'https://api.mch.weixin.qq.com/pay/unifiedorder'
    goodsIntroduce = goodsIntroduce.encode(encoding='utf8')
    print('goodsIntroduce===========> ',goodsIntroduce)
    result_data = {
        'appid': 'wx1add8692a23b5976', # appid
        'mch_id': '1513325051', # 商户号
        'nonce_str': timeStamp,      # 32位随机值
        # 'sign': '',             # 签名
        'body': goodsIntroduce,
        'out_trade_no': getWxPayOrderId,
        'total_fee': amount,
        'spbill_create_ip': spbillIp,
        'notify_url': 'http://api.zhugeyingxiao.com/zhugeleida/xiaochengxu/pay',
        'trade_type': 'JSAPI'
        }
    stringSignTemp = shengchengsign(result_data)
    result_data['sign'] = md5(stringSignTemp).upper()
    xml_data = toXml(result_data)

    print('xml_data------------------> ',xml_data)
    ret = requests.post(url, data=xml_data, headers={'Content-Type': 'text/xml'})
    ret.encoding = 'utf8'
    # print('-ret.text------------>',ret.text)
    DOMTree = xmldom.parseString(ret.text)
    collection = DOMTree.documentElement
    # code_url = collection.getElementsByTagName("code_url")[0].childNodes[0].data  # 二维码链接

    prepay_id = collection.getElementsByTagName("prepay_id")[0].childNodes[0].data  # 直接支付
    timeStamp = generateRandomStamping()  # 时间戳
    data_dict = {
        'appId' : 'wx202b03ae2fbf636f',
        'timeStamp': '20180925160609',
        'nonceStr':timeStamp,
        'package': prepay_id,
        'signType': 'MD5'
    }
    stringSignTemp = shengchengsign(data_dict)
    data_dict['paySign'] = md5(stringSignTemp).upper()
    response.code = 200
    response.data = data_dict
    return JsonResponse(response.__dict__)



