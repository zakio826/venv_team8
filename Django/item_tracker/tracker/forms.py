import os

from django.contrib.auth.mixins import LoginRequiredMixin

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

from django import http

class AssetCreateForm(forms.ModelForm, http.HttpRequest):

    class Meta:
        model = Asset
        fields = ['asset_name', 'group']
        
    def __init__(self, *args, **kwargs):
        # self.current_user = user
        super().__init__(*args, **kwargs)
        # print("fff", kwargs['instance'])
        # print("ooo", user)
        # print("uuu", self)
        # print("rrr", Group.objects.filter(user=user))
        # print("aaa", self.fields['group'].queryset)
        # self.fields['group'].queryset = Group.objects.filter(user=user)
        # print("uuu", self.fields['group'].queryset)

        self.fields['group'].widget.attrs['class'] = 'form-control'
        self.fields['asset_name'].widget.attrs['class'] = 'form-control'

    # def method(self):
    #     model = Asset
    #     model.objects.filter(user=self.current_user)