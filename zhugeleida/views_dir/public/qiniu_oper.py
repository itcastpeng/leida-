from publicFunc import Response
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt, csrf_protect

import datetime as dt, time, json, uuid, os, base64
from zhugeleida.views_dir.public.watermark import encryption
import qiniu, requests
from publicFunc.account import randon_str
from qiniu import put_file

# 内部调用
def qiniu_get_token(img_path, key=None):
    SecretKey = 'wVig2MgDzTmN_YqnL-hxVd6ErnFhrWYgoATFhccu'
    AccessKey = 'a1CqK8BZm94zbDoOrIyDlD7_w7O8PqJdBHK-cOzz'
    q = qiniu.Auth(AccessKey, SecretKey)
    bucket_name = 'bjhzkq_tianyan'
    # key = randon_str()
    # policy = {  # 指定上传文件的格式 等
    #
    # }
    if not key:
        token = q.upload_token(bucket_name)  # 可以指定key 图片名称
        data = {
            'token': token
        }
    else:
        token = q.upload_token(bucket_name, key, 3600)  # 可以指定key 图片名称
        data = {
            'token': token,
            'key': key,
        }
    # token = q.upload_token(bucket_name)  # 可以指定key 图片名称
    # token = q.upload_token(bucket_name, None, 3600, policy)  # 可以指定key 图片名称
    # print('qiniu_url------qiniu_url------------qiniu_url-----------qiniu_url---------qiniu_url---------> ')
    # ret, info = put_file(token, None, mime_type="text/js", file_path=img_path)
    # print('ret.content-==========2@@@@@@@@@@@@@@@@@@@@!!!!!!!!!!!!!!!!!!##################$$$$$$$$$$$$$$$$$$$$$+=====》', ret)

    # ret, info = put_file(token, key, img_path)
    qiniu_url = 'https://up-z1.qiniup.com/'
    # data = {
    #     'token': token,
    # }
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13'
    }
    files = {
        'file': open(img_path, 'rb')
    }
    ret = requests.post(qiniu_url, data=data, files=files, headers=headers)
    print('###############@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#################_------------> ', ret.text, data)
    if 'http://tianyan.zhugeyingxiao.com/' not in img_path and os.path.exists(img_path):
        os.remove(img_path)  # 删除本地图片
    img_path = 'http://tianyan.zhugeyingxiao.com/' + ret.json().get('key')
    return img_path

# 前端请求
def qiniu_oper(request, oper_type):
    response = Response.ResponseObj()
    if oper_type == 'qiniu_token':
        SecretKey = 'wVig2MgDzTmN_YqnL-hxVd6ErnFhrWYgoATFhccu'
        AccessKey = 'a1CqK8BZm94zbDoOrIyDlD7_w7O8PqJdBHK-cOzz'
        q = qiniu.Auth(AccessKey, SecretKey)
        bucket_name = 'bjhzkq_tianyan'
        token = q.upload_token(bucket_name)  # 可以指定key 图片名称
        response.code = 200
        response.msg = 'token生成完成'
        response.data = {
            'token': token,
        }

    return JsonResponse(response.__dict__)


def requests_video_download(url):
    print('----------下载视频-------------> ', url)
    img_save_path = randon_str() + '.mp4'
    # img_save_path = '2.mp4'
    r = requests.get(url, stream=True)
    # print('r----> ', r.text)
    with open(img_save_path, "wb") as mp4:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                mp4.write(chunk)

    return img_save_path

# 请求图片地址保存本地
def requests_img_download(old_url):
    ret = requests.get(old_url)
    path = os.path.join('statics', 'zhugeleida', 'imgs', 'admin', randon_str() + '.png')
    with open(path, 'wb') as e:
        e.write(ret.content)
    return path



if __name__ == '__main__':
    ret = qiniu_get_token('1.jpg')
    print('ret------> ', ret)





















