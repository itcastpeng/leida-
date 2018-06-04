from django.conf.urls import url

from zhugeleida.views_dir import login, role, user,quanxian,company,tag,user_weixin_auth,customer,chat


urlpatterns = [
    url(r'^login$', login.login),

    # 权限操作
    url(r'^quanxian/(?P<oper_type>\w+)/(?P<o_id>\d+)', quanxian.quanxian_oper),
    url(r'^quanxian', quanxian.quanxian),

    # 角色操作
    url(r'^role/(?P<oper_type>\w+)/(?P<o_id>\d+)', role.role_oper),
    url(r'^role$', role.role),

    # 用户操作
    url(r'^user/(?P<oper_type>\w+)/(?P<o_id>\d+)', user.user_oper),
    url(r'^user', user.user),

    # 公司操作
    url(r'^company/(?P<oper_type>\w+)/(?P<o_id>\d+)', company.company_oper),
    url(r'^company$', company.company),

    # 标签操作
    url(r'^tag/(?P<oper_type>\w+)/(?P<o_id>\d+)', tag.tag_oper),
    url(r'^tag$', tag.tag),

    # /customer/add/0  添加客户信息
    # /customer/update/1  修改客户信息   tag_list=[1,2]  chengjiaoriqi=   gailv=
    # /customer/update_xiangqing/1  修改客户信息   create / update

    url(r'^customer/(?P<oper_type>\w+)/(?P<o_id>\d+)', customer.customer_oper),
    url(r'^customer$', customer.customer),

    url(r'^chat/(?P<oper_type>\w+)/(?P<o_id>\d+)', chat.chat_oper),
    url(r'^chat$',chat.chat),

    #企业微信网页登录认证
    # url(r'^work_weixin_auth/(?P<oper_type>\w+)/(?P<o_id>\d+)', work_weixin_auth.work_weixin_auth_oper),
    url(r'^work_weixin_auth/(?P<company_id>\d+)', user_weixin_auth.work_weixin_auth)

]
