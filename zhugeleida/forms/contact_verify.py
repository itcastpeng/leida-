from django import forms

from zhugeleida import models
from publicFunc import account
import datetime
import re
from django.core.exceptions import ValidationError


# 判断是否是数字
class ContactSelectForm(forms.Form):
    user_id = forms.IntegerField(
        required=True,
        error_messages= {
            'invalid': "用户ID不能为空",
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