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
        fields = ['group', 'asset', 'user', 'image', 'taken_at', 'front']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget = forms.HiddenInput()
        self.fields['asset'].widget = forms.HiddenInput()
        self.fields['front'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ItemAddForm(forms.ModelForm):
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
        fields = ['group', 'asset', 'item_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget = forms.HiddenInput()
        self.fields['asset'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.fields['finish'].widget.attrs['class'] = 'form-choice-input'




class ItemAddDummyForm(forms.ModelForm):
    name = forms.CharField(label='アイテム名', max_length=30)

class ItemAddEXForm(forms.ModelForm):
    
    class Meta:
        model = Item
        fields = ['group', 'asset', 'item_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget = forms.HiddenInput()
        self.fields['asset'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    # def save(self, group, asset, item_list):
    #     obj = super.save(commit=False)
    #     for name in item_list:
    #         obj.item_name = name
    #         obj.save()
    #     return obj








class AssetMultiCreateForm(MultiModelForm):

    form_classes = {
        "asset_create_form": AssetCreateForm,
        "image_add_form": ImageAddForm,
        "item_add_form": ItemAddEXForm,
    }


class ItemMultiAddForm(MultiModelForm):

    form_classes = {
        "image_add_form": ImageAddForm,
        "item_add_form": ItemAddForm,
    }








class GroupJoinForm(forms.ModelForm):

    class Meta:
        model = GroupMember
        fields = ['group']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].widget.attrs['class'] = 'form-control'
