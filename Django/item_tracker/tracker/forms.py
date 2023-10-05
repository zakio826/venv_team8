import os
from typing import Any

from betterforms.multiform import MultiModelForm

from django import forms
from django.core.mail import EmailMessage

from accounts.models import CustomUser
from .models import Group, GroupMember, Asset, Item, Image, History, Result


class InquiryForm(forms.Form):
    name = forms.CharField(label='お名前', max_length=30)
    email = forms.EmailField(label='メールアドレス')
    title = forms.CharField(label='タイトル', max_length=30)
    message = forms.CharField(label='メッセージ', widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['name'].widget.attrs['placeholder'] = 'お名前をここに入力してください。'

        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'メールアドレスをここに入力してください。'

        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['title'].widget.attrs['placeholder'] = 'タイトルをここに入力してください。'

        self.fields['message'].widget.attrs['class'] = 'form-control'
        self.fields['message'].widget.attrs['placeholder'] = 'メッセージをここに入力してください。'
        self.fields['message'].widget.attrs['style'] = 'height: 10rem'


    def send_email(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        title = self.cleaned_data['title']
        message = self.cleaned_data['message']
        
        subject = 'お問い合わせ {}'.format(title)
        message = '送信者名: {0}\nメールアドレス: {1}\nメッセージ:\n{2}'.format(name, email, message)
        from_email = os.environ.get('FROM_EMAIL')
        to_list = [
            os.environ.get('FROM_EMAIL')
        ]
        cc_list = [
            email
        ]

        message = EmailMessage(subject=subject, body=message, from_email=from_email, to=to_list, cc=cc_list)
        message.send()

from django.contrib.auth.mixins import LoginRequiredMixin

class AssetCreateForm(LoginRequiredMixin, forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_name', 'group']

    def __init__(self, *args, **kwargs):
        # kwargs={'instance': self.request.user}
        super().__init__(*args, **kwargs)
        self.fields['group'].widget.attrs['class'] = 'form-control'
        self.fields['asset_name'].widget.attrs['class'] = 'form-control'

class ImageAddForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image', 'group', 'asset', 'user', 'taken_at', 'front']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget = forms.HiddenInput()
        self.fields['asset'].widget = forms.HiddenInput()
        self.fields['front'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
    # def save(self, group=None, asset=None):
    #     obj = super.save(commit=False)
    #     if group and asset:
    #         obj.group = group
    #         obj.asset = asset
    #     obj.save()
    #     return obj

class ItemAddForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ['group', 'asset', 'item_name', 'outer_edge']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget = forms.HiddenInput()
        self.fields['asset'].widget = forms.HiddenInput()
        self.fields['outer_edge'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        # self.fields['finish'].widget.attrs['class'] = 'form-choice-input'

class ItemAddEXForm(forms.ModelForm):
    finish = forms.ChoiceField(
        label='続ける',
        required=False,
        # disabled=False,
        initial=[0],
        choices=[(0, 'はい、続けます。'), (1, 'いいえ、終了します。')],
        widget=forms.RadioSelect()
    )
    
    class Meta:
        model = Item
        fields = ['group', 'asset', 'item_name', 'outer_edge']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget = forms.HiddenInput()
        self.fields['asset'].widget = forms.HiddenInput()
        # self.fields['item_list'].widget = forms.HiddenInput()
        self.fields['outer_edge'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['finish'].widget.attrs['class'] = 'form-choice-input'
    
    # def save(self, group=None, asset=None, item_list=None):
    #     obj = super.save(commit=False)
    #     if group and asset and item_list:
    #         obj.item_list = item_list
    #         obj.group = group
    #         obj.asset = asset
    #         for name in obj.item_list:
    #             obj.item_name = name
    #             obj.save()
    #     else:
    #         for name in obj.item_list:
    #             obj.item_name = name
    #             obj.save()
    #     return obj
    
    # def save(self, group, asset, item_list):
    #     obj = super.save(commit=False)
    #     for name in item_list:
    #         obj.item_name = name
    #         obj.save()
    #     return obj

class HistoryAddForm(forms.ModelForm):

    class Meta:
        model = History
        fields = ['group', 'asset', 'user', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.fields['update_at'].widget = forms.HiddenInput()
        # self.fields['group'].widget = forms.HiddenInput()
        # self.fields['asset'].widget = forms.HiddenInput()
        # self.fields['user'].widget = forms.HiddenInput()
        # self.fields['image'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget = forms.HiddenInput()

class ResultAddForm(forms.ModelForm):

    class Meta:
        model = Result
        fields = ['asset', 'item', 'image', 'result_class', 'box_x_min', 'box_y_min', 'box_x_max', 'box_y_max']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['asset'].widget = forms.HiddenInput()
        # self.fields['item'].widget = forms.HiddenInput()
        self.fields['image'].widget = forms.HiddenInput()
        self.fields['result_class'].widget = forms.HiddenInput()
        # self.fields['box_x_min'].widget = forms.HiddenInput()
        # self.fields['box_y_min'].widget = forms.HiddenInput()
        # self.fields['box_x_max'].widget = forms.HiddenInput()
        # self.fields['box_y_max'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget = forms.HiddenInput()

# class HistoryMultiAddForm(MultiModelForm):

#     form_classes = {
#         "history_add_form": HistoryAddForm,
#         "result_add_form": forms.formset_factory(
#             form = 
#         ),
#     }







class ItemAddDummyForm(forms.ModelForm):
    name = forms.CharField(label='アイテム名', max_length=30)








from collections import OrderedDict

class AssetMultiCreateForm(MultiModelForm):

    form_classes = {
        "asset_create_form": AssetCreateForm,
        "image_add_form": ImageAddForm,
        "item_add_form": ItemAddEXForm,
    }

    # def save(self, group=None, asset=None, item_list=None):
    #     obj = super.save(commit=False)
    #     print("ttt", obj)

    #     objects = OrderedDict(
    #         (key, form.save())
    #         for key, form in self.forms.items()
    #     )

    #     if any(hasattr(form, 'save_m2m') for form in self.forms.values()):
    #         def save_m2m():
    #             for form in self.forms.values():
    #                 if hasattr(form, 'save_m2m'):
    #                     form.save_m2m()
    #         self.save_m2m = save_m2m

    #     return objects


class ItemMultiAddForm(MultiModelForm):

    form_classes = {
        "image_add_form": ImageAddForm,
        "item_add_form": ItemAddForm,
    }




class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name', 'private']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # デフォルト値をNoneに設定
        super().__init__(*args, **kwargs)
        self.fields['private'].initial = False
        self.fields['private'].widget = forms.HiddenInput()
        if user:
            self.fields['user'].initial = user

class JoinGroupForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.filter(private=False),  # 個人利用でないグループを選択
        label='グループ選択',
    )





class GroupJoinForm(forms.ModelForm):

    class Meta:
        model = GroupMember
        fields = ['group']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget.attrs['class'] = 'form-control'
