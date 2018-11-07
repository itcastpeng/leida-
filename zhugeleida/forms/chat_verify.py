from django import forms

from zhugeleida import models
from publicFunc import account
import datetime
import re
from django.core.exceptions import ValidationError


# 判断是否是数字
class ChatSelectForm(forms.Form):
    user_id = forms.IntegerField(
        required=True,
        error_messages= {
            'invalid': "用户ID不能为空",
        }
    )



    customer_id = forms.IntegerField(
        required=True,
        error_messages={
            'invalid': "客户ID不能为空",
        }
    )

    current_page = forms.IntegerField(
        required=False,
        error_messages={
            'invalid': "页码数据类型错误",
        }
    )
    length = forms.IntegerField(
        required=False,
        error_messages={
            'invalid': "页显示数量类型错误"
        }
    )

    def clean_current_page(self):
        if 'current_page' not in self.data:
            current_page = 1
        else:
            current_page = int(self.data['current_page'])
        return current_page

    def clean_length(self):
        if 'length' not in self.data:
            length = 20
        else:
            length = int(self.data['length'])
        return length

    # # 判断用户id是否存在
    # def clean_user_id(self):
    #
    #     user_id = self.data['user_id']
    #
    #     objs = models.zgld_userprofile.objects.filter(
    #         id=user_id,
    #     )
    #     if not objs:
    #         self.add_error('username', '用户名不存在')
    #     else:
    #         return user_id

    # 判断用户名是否存在
    def clean_customer_id(self):

        customer_id = self.data['customer_id']

        objs = models.zgld_customer.objects.filter(
            id=customer_id,
        )
        if not objs:
            self.add_error('customer_id', '客户不存在')
        else:
            return customer_id


class ChatPostForm(forms.Form):
    customer_id = forms.IntegerField(
        required=True,
        error_messages={
            'invalid': "客户ID不能为空",
        }
    )
    send_type = forms.IntegerField(
        required=False,
        error_messages={
            'invalid': "发送类型不能为空",
        }
    )

    content = forms.CharField(
        required=True,
        error_messages={
            'required': "消息不能为空"
        }
    )
    msg = forms.CharField(
        required=False,
        error_messages={
            'required': "消息不能为空"
        }
    )

    # # 判断用户id是否存在
    # def clean_user_id(self):
    #
    #     user_id = self.data['u_id']
    #
    #     objs = models.zgld_userprofile.objects.filter(
    #         id=user_id,
    #     )
    #     if not objs:
    #         self.add_error('username', '用户名不存在')
    #     else:
    #         return user_id


# 判断是否是数字
class ChatGetForm(forms.Form):
    user_id = forms.IntegerField(
        required=True,
        error_messages= {
            'invalid': "用户ID不能为空",
        }
    )


    customer_id = forms.IntegerField(
        required=True,
        error_messages={
            'invalid': "客户ID不能为空",
        }
    )


    # 判断用户id是否存在
    # def clean_user_id(self):
    #
    #     user_id = self.data['user_id']
    #
    #     objs = models.zgld_userprofile.objects.filter(
    #         id=user_id,
    #     )
    #     if not objs:
    #         self.add_error('username', '用户名不存在')
    #     else:
    #         return user_id
    #
    # # 判断用户名是否存在
    # def clean_customer_id(self):
    #
    #     customer_id = self.data['user_id']
    #
    #     objs = models.zgld_customer.objects.filter(
    #         id=customer_id,
    #     )
    #     if not objs:
    #         self.add_error('customer_id', '客户不存在')
    #     else:
    #         return customer_id