from django import forms
from zhugeleida import models
from publicFunc import account
import datetime
import re
import json
from django.core.exceptions import ValidationError

# 添加企业的产品
class SetFocusGetRedPacketForm(forms.Form):

    is_focus_get_redpacket = forms.CharField(
        required=True,
        error_messages={
            'required': "关注领取红包是否开启不能为空"
        }
    )

    focus_get_money = forms.FloatField(
        required=False,
        error_messages={
            'required': "关注领取红包金额不能为空"
        }
    )

    max_single_money = forms.FloatField(
        required=False,
        error_messages={
            'required': "随机单个金额(元)不能为空"
        }
    )

    min_single_money = forms.FloatField(
        required=False,
        error_messages={
            'required': "随机单个金额(元)不能为空"
        }
    )

    focus_total_money = forms.IntegerField(
        required=True,
        error_messages={
            'required': "领取红包总金额不能为空"
        }
    )

    def clean_max_single_money(self):
        max_single_money = self.data['max_single_money']
        mode = self.data['mode']

        if  max_single_money:
            max_single_money = float(max_single_money)

            if max_single_money < 0.3 or max_single_money  > 200:
                self.add_error('max_single_money', '红包金额不能小于0.3元或大于200元')

            else:
                return max_single_money

        else:
            mode = int(mode)
            if mode == 1: #随机金额
                self.add_error('max_single_money', '最大随机金额不能为空')

    def clean_min_single_money(self):
        min_single_money = self.data['min_single_money']
        mode = self.data['mode']

        if  min_single_money:
            min_single_money = float(min_single_money)

            if min_single_money < 0.3 or min_single_money  > 200:
                self.add_error('max_single_money', '红包金额不能小于0.3元或大于200元')

            else:
                return min_single_money

        else:
            mode = int(mode)
            if mode == 1: #随机金额
                self.add_error('min_single_money', '最大随机金额不能为空')

    def clean_focus_get_money(self):
        focus_get_money = self.data['focus_get_money']
        mode = self.data['mode']

        if focus_get_money:
            focus_get_money = float(focus_get_money)

            if focus_get_money < 0.3 or focus_get_money  > 200:
                self.add_error('focus_get_money', '红包金额不能小于0.3元或大于200元')

            else:

                return focus_get_money
        else:
            mode = int(mode)
            if mode == 2:  # 固定金额
                self.add_error('focus_get_money', '固定金额不能为空')




#增加日记列表
class CaseAddForm(forms.Form):


    case_name = forms.CharField(
        required=True,
        error_messages={
            'required': "案例名称不能为空"
        }
    )

    customer_name = forms.CharField(
        required=True,
        error_messages={
            'required': "客户名字不能为空"
        }
    )

    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
        }
    )

    status = forms.IntegerField(
        required=True,
        error_messages={
            'required': "状态不能为空"
        }
    )

    headimgurl  = forms.CharField(
        required=True,
        error_messages={
            'required': "头像不能为空"
        }
    )

    case_type  = forms.IntegerField(
        required=True,
        error_messages={
            'required': "案例类型不能为空"
        }
    )

    tags_id_list = forms.CharField(
        required=True,
        error_messages={
            'required': "案例标签不能为空"
        }
    )
    become_beautiful_cover = forms.CharField(
        required=False,
        error_messages={
            'required': "变美图片类型错误"
        }
    )
    cover_picture = forms.CharField(
        required=False,
        error_messages={
            'required': "封面图片类型错误"
        }
    )
    def clean_case_name(self):

        company_id = self.data['company_id']
        case_name =  self.data['case_name']

        objs = models.zgld_case.objects.filter(
            case_name=case_name, company_id=company_id,status=1
        )

        if objs:
            self.add_error('case_name', '不能存在相同的案例名')
        else:
            return case_name

    def clean_tags_id_list(self):
        tags_id_list = self.data.get('tags_id_list')
        tags_id_list = json.loads(tags_id_list)
        if len(tags_id_list) <= 0:
            self.add_error('tags_id_list', '标签不能为空')
        else:
            return tags_id_list

    def clean_case_type(self):
        case_type = int(self.data.get('case_type'))          # 日记列表类型
        become_beautiful_cover = self.data.get('become_beautiful_cover')  # 变美图片
        cover_picture = self.data.get('cover_picture')  # 封面
        if case_type == 2: # 时间轴日记
            if not become_beautiful_cover:
                self.add_error('become_beautiful_cover', '变美图片不能为空')
            if not cover_picture:
                self.add_error('cover_picture', '封面图片不能为空')
        return case_type

# 修改日记列表
class CaseUpdateForm(forms.Form):

    case_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "案例ID不能为空"
        }
    )

    case_name = forms.CharField(
        required=True,
        error_messages={
            'required': "案例名称不能为空"
        }
    )

    customer_name = forms.CharField(
        required=True,
        error_messages={
            'required': "客户名字不能为空"
        }
    )

    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
        }
    )

    status = forms.IntegerField(
        required=True,
        error_messages={
            'required': "状态不能为空"
        }
    )

    headimgurl = forms.CharField(
        required=True,
        error_messages={
            'required': "头像不能为空"
        }
    )
    case_type = forms.IntegerField(
        required=True,
        error_messages={
            'required': "案例类型不能为空"
        }
    )

    tags_id_list = forms.CharField(
        required=True,
        error_messages={
            'required': "案例标签不能为空"
        }
    )
    become_beautiful_cover = forms.CharField(
        required=False,
        error_messages={
            'required': "变美图片类型错误"
        }
    )
    cover_picture = forms.CharField(
        required=False,
        error_messages={
            'required': "封面图片类型错误"
        }
    )

    def clean_case_name(self):

        case_id = self.data['case_id']
        company_id = self.data['company_id']
        case_name = self.data['case_name']

        objs = models.zgld_case.objects.filter(
            case_name=case_name, company_id=company_id,status=1
        ).exclude(id=case_id)

        if objs:
            self.add_error('case_name', '不能存在相同的案例名')
        else:
            return case_name

    def clean_case_type(self):
        case_type = int(self.data.get('case_type'))  # 日记列表类型
        become_beautiful_cover = self.data.get('become_beautiful_cover')  # 变美图片
        cover_picture = self.data.get('cover_picture')  # 封面
        if case_type == 2:  # 时间轴日记
            if not become_beautiful_cover:
                self.add_error('become_beautiful_cover', '变美图片不能为空')
            if not cover_picture:
                self.add_error('cover_picture', '封面图片不能为空')
        return case_type

    def clean_tags_id_list(self):
        tags_id_list = self.data.get('tags_id_list')
        tags_id_list = json.loads(tags_id_list)
        if len(tags_id_list) <= 0:
            self.add_error('tags_id_list', '标签不能为空')
        else:
            return tags_id_list


class PosterSettingForm(forms.Form):
    case_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "案例ID不能为空"
        }
    )

    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
        }
    )

    poster_cover = forms.CharField(
        required=True,
        error_messages={
            'required': "海报图片不能为空"
        }
    )
    def clean_poster_cover(self):
        poster_cover = self.data.get('poster_cover')
        json_poster_cover = json.loads(poster_cover)
        if len(json_poster_cover) in [1, 2, 9]:
            return poster_cover
        else:
            self.add_error('poster_cover', '请控制图片 在1张 2张 9张')





#修改活动
class ActivityUpdateForm(forms.Form):
    article_id = forms.IntegerField(
        required=False,
        error_messages={
            'required': "文章ID不能为空"
        }
    )
    mode  = forms.IntegerField(
        required=True,
        error_messages={
            'required': "红包发送方式不能为空"
        }
    )

    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
        }
    )

    activity_name = forms.CharField(
        required=True,
        error_messages={
            'required': "活动名称不能为空"
        }
    )

    activity_id = forms.CharField(
        required=True,
        error_messages={
            'required': "活动ID不能为空"
        }
    )


    activity_total_money = forms.IntegerField(
        required=True,
        error_messages={
            'required': "活动总金额不能为空"
        }
    )

    activity_single_money = forms.FloatField(
        required=False,
        error_messages={
            'required': "单个金额(元)不能为空"
        }
    )

    max_single_money = forms.FloatField(
        required=False,
        error_messages={
            'required': "随机单个金额(元)不能为空"
        }
    )

    min_single_money = forms.FloatField(
        required=False,
        error_messages={
            'required': "随机单个金额(元)不能为空"
        }
    )

    reach_forward_num = forms.IntegerField(
        required=True,
        error_messages={
            'required': "设置转发次数不能为空"
        }
    )

    start_time = forms.CharField(
        required=True,
        error_messages={
            'required': "设置转发次数不能为空"
        }
    )

    end_time = forms.CharField(
        required=True,
        error_messages={
            'required': "设置转发次数不能为空"
        }
    )

    reach_stay_time = forms.IntegerField(
        required=True,
        error_messages={
            'required': " 限制时间秒数 不能为空"
        }
    )

    is_limit_area = forms.CharField(
        required=True,
        error_messages={
            'required': "是否限制区域 不能为空"
        }
    )


    # 判断文章是否存在
    def clean_article_id(self):
        article_id = self.data['article_id']
        objs = models.zgld_article.objects.filter(id = article_id)

        if  not objs:
            self.add_error('article_id', '此文章不存在')

        else:
            return article_id

    def clean_activity_id(self):
        activity_id = self.data['activity_id']
        objs = models.zgld_article_activity.objects.filter(id = activity_id)

        if  not objs:
            self.add_error('activity_id', '此活动不存在')

        else:
            return activity_id

    def clean_max_single_money(self):
        max_single_money = self.data['max_single_money']
        mode = self.data['mode']

        if max_single_money:
            max_single_money = float(max_single_money)

            if max_single_money < 0.3 or max_single_money > 200:
                self.add_error('max_single_money', '红包金额不能小于0.3元或大于200元')

            else:
                return max_single_money

        else:
            mode = int(mode)
            if mode == 1:  # 随机金额
                self.add_error('max_single_money', '最大随机金额不能为空')

    def clean_min_single_money(self):
        min_single_money = self.data['min_single_money']
        mode = self.data['mode']

        if min_single_money:
            min_single_money = float(min_single_money)

            if min_single_money < 0.3 or min_single_money > 200:
                self.add_error('max_single_money', '红包金额不能小于0.3元或大于200元')

            else:
                return min_single_money

        else:
            mode = int(mode)
            if mode == 1:  # 随机金额
                self.add_error('min_single_money', '最大随机金额不能为空')

    def clean_activity_single_money(self):
        activity_single_money = self.data['activity_single_money']
        mode = self.data['mode']

        if activity_single_money:
            activity_single_money = float(activity_single_money)

            if activity_single_money < 0.3 or activity_single_money > 200:
                self.add_error('activity_single_money', '红包金额不能小于0.3元或大于200元')

            else:

                return activity_single_money
        else:
            mode = int(mode)
            if mode == 2:  # 固定金额
                self.add_error('activity_single_money', '固定金额不能为空')



class CaseSelectForm(forms.Form):


    current_page = forms.IntegerField(
        required=False,
        error_messages={
            'required': "页码数据类型错误",
        }
    )
    length = forms.IntegerField(
        required=False,
        error_messages={
            'required': "页显示数量类型错误"
        }
    )
    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
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


class QueryFocusCustomerSelectForm(forms.Form):


    current_page = forms.IntegerField(
        required=False,
        error_messages={
            'required': "页码数据类型错误",
        }
    )
    length = forms.IntegerField(
        required=False,
        error_messages={
            'required': "页显示数量类型错误"
        }
    )
    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
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



class ArticleRedPacketSelectForm(forms.Form):


    current_page = forms.IntegerField(
        required=False,
        error_messages={
            'required': "页码数据类型错误",
        }
    )
    length = forms.IntegerField(
        required=False,
        error_messages={
            'required': "页显示数量类型错误"
        }
    )
    company_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "公司ID不能为空"
        }
    )

    article_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "文章ID不能为空"
        }
    )

    activity_id = forms.IntegerField(
        required=True,
        error_messages={
            'required': "活动ID不能为空"
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




