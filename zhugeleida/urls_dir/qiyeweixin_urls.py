from django.conf.urls import url

from zhugeleida.views_dir.qiyeweixin import user, quanxian, action, tag_customer, user_weixin_auth, customer, tongxunlu, \
    qr_code_auth, follow_language, follow_info, tag_list, article, talkGroupManagement, speechDetailsManagement, oper_log, \
    record_video

from zhugeleida.views_dir.qiyeweixin import chat, contact, search, mingpian, tag_user, product, theOrderManagement
from zhugeleida.views_dir.public import websocket

urlpatterns = [

    # # 权限操作
    # url(r'^quanxian/(?P<oper_type>\w+)/(?P<o_id>\d+)$', quanxian.quanxian_oper),
    # url(r'^quanxian$', quanxian.quanxian),

    # # 用户操作
    # url(r'^user/(?P<oper_type>\w+)/(?P<o_id>\d+)$', user.user_oper),
    # url(r'^user$', user.user),

    # # 标签 和 标签用户的操作
    # url(r'^tag_user/(?P<oper_type>\w+)$', tag_user.tag_user_oper),
    # url(r'^tag_user$', tag_user.tag_user),

    # # 搜索(客户\标签)
    # url(r'^search/(?P<oper_type>\w+)$', search.search),

    # 通讯录-公众号标签
    url(r'^tag_customer/(?P<oper_type>\w+)/(?P<o_id>\d+)$', tag_customer.tag_customer_oper),
    url(r'^tag_customer$', tag_customer.tag_customer),

    # 标签列表和标签列表的的操作
    url(r'^tag_list/(?P<oper_type>\w+)/(?P<o_id>\d+)$', tag_list.tag_list_oper),
    url(r'^tag_list$', tag_list.tag_list),


    # 修改客户详情和客户关联信息表
    url(r'^customer/(?P<oper_type>\w+)/(?P<o_id>\d+)$', customer.customer_oper),
    url(r'^customer$', customer.customer),  # 查询用户详细信息

    # 通讯录列表
    url(r'^tongxunlu$', tongxunlu.tongxunlu),

    # 用户跟进常用语
    url(r'follow_language/(?P<oper_type>\w+)/(?P<o_id>\d+)$', follow_language.follow_language_oper),
    url(r'follow_language$', follow_language.follow_language),

    # 用户跟进信息
    url(r'follow_info/(?P<oper_type>\w+)/(?P<o_id>\d+)$', follow_info.follow_info_oper),
    url(r'follow_info$', follow_info.follow_info),

    # 实时聊天 一对多
    url(r'^chat/(?P<oper_type>\w+)/(?P<o_id>\d+)', chat.chat_oper),
    url(r'^chat$', chat.chat),

    # 获取消息客户列表
    url(r'^contact/(?P<oper_type>\w+)$', contact.contact_oper),
    url(r'^contact$', contact.contact),

    url(r'^websocket/(?P<oper_type>\w+)$', websocket.leida_websocket),

    # 我的订单管理查询
    url(r'theOrder$', theOrderManagement.theOrder),

    # 获取访问日志动作。
    url(r'^action/(?P<oper_type>\w+)$', action.action),

    # 生成微信二维码 create_qr_code
    url(r'^qr_code_auth$', qr_code_auth.create_qr_code),

    # 企业微信网页登录认证 --- 疑问
    # url(r'^work_weixin_auth/(?P<company_id>\d+)$', user_weixin_auth.work_weixin_auth),
    url(r'^work_weixin_auth/(?P<oper_type>\w+)$', user_weixin_auth.work_weixin_auth_oper),  # 创建公众号分享url

    # # 企业微信JS-SDK使用权限签名算法
    # url(r'^enterprise_weixin_sign$', user_weixin_auth.enterprise_weixin_sign),

    # 访问企业微信-我的用户名片
    url(r'^mingpian/(?P<oper_type>\w+)$', mingpian.mingpian_oper),
    url(r'^mingpian$', mingpian.mingpian),

    # 企业产品操作
    url(r'^product/(?P<oper_type>\w+)/(?P<o_id>\d+)$', product.product_oper),
    url(r'^product/(?P<oper_type>\w+)$', product.product),

    # 企业微信端-文章管理
    url(r'^article/(?P<oper_type>\w+)/(?P<o_id>\d+)$', article.article_oper),
    url(r'^article/(?P<oper_type>\w+)$', article.article),

    # 聊天页-话术库-分组
    url(r'^talkGroupManage$', talkGroupManagement.talkGroupManage),
    # url(r'^talkGroupManageOper/(?P<oper_type>\w+)/(?P<o_id>\d+)$', talkGroupManagement.talkGroupManageOper),

    # 聊天页-话术库-详情
    url(r'^speechDetailsManage$', speechDetailsManagement.speechDetailsManage),

    # 记录用户(咨询)操作日志
    url(r'^oper_log/(?P<oper_type>\w+)/(?P<o_id>\d+)$', oper_log.oper_log_oper),
    url(r'^customer_oper_article/(?P<oper_type>\w+)$', oper_log.update_click_dialog_num), # 记录客户点击咨询对话框 次数(文章分享里)

    # 录播视频
    url(r'^record_video/(?P<oper_type>\w+)/(?P<o_id>\d+)$', record_video.record_video_oper),            # 视频操作
    url(r'^record_video$', record_video.record_video),                                                  # 视频查询

]
