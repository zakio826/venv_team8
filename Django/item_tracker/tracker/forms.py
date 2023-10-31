import os
from typing import Any

from betterforms.multiform import MultiModelForm
from django.conf import settings

from django import forms
from django.core.mail import EmailMessage

from django.conf import settings

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

class GroupFilterForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),  # 最初は空のクエリセット
        empty_label='すべてのグループ',
        required=False,
        label='グループ'
    )

    def __init__(self, user, *args, **kwargs):
        super(GroupFilterForm, self).__init__(*args, **kwargs)
        # ユーザーが所属しているすべてのグループを取得し、クエリセットを設定
        self.fields['group'].queryset = Group.objects.filter(groupmember__user=user)

class SortForm(forms.Form):
    choices = [
        ('', 'ソート順を選択'),
        ('asc', '昇順'),
        ('desc', '降順'),
    ]
    sort_order = forms.ChoiceField(choices=choices, required=False, label='ソート順')
class AssetCreateForm(LoginRequiredMixin, forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_name', 'group']

    def __init__(self, *args, **kwargs):
        # kwargs={'instance': self.request.user}
        super().__init__(*args, **kwargs)
        self.fields['group'].widget.attrs['class'] = 'form-control'
        self.fields['asset_name'].widget.attrs['class'] = 'form-control'

class ItemAddForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['item_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.fields['group'].widget = forms.HiddenInput()
        # self.fields['asset'].widget = forms.HiddenInput()
        # self.fields['outer_edge'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    # def save(self):
    #     obj = super.save(commit=False)
    #     if obj.outer_edge:
    #         obj.item_name = "外枠"
    #     obj.save()
    #     return obj

# class ItemAddEXForm(forms.ModelForm):
#     finish = forms.ChoiceField(
#         label='続ける',
#         required=False,
#         # disabled=False,
#         initial=[0],
#         choices=[(0, 'はい、続けます。'), (1, 'いいえ、終了します。')],
#         widget=forms.RadioSelect()
#     )
    
#     class Meta:
#         model = Item
#         fields = ['group', 'asset', 'item_name', 'outer_edge']
        
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.fields['group'].widget = forms.HiddenInput()
#         self.fields['asset'].widget = forms.HiddenInput()
#         # self.fields['item_list'].widget = forms.HiddenInput()
#         self.fields['outer_edge'].widget = forms.HiddenInput()

#         for field in self.fields.values():
#             field.widget.attrs['class'] = 'form-control'
        
#         self.fields['finish'].widget.attrs['class'] = 'form-choice-input'
    
class ImageAddForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['movie', 'user', 'taken_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['movie'].widget.attrs['accept'] = ".mp4"

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_file(self):
        file = self.cleaned_data['file']
        extension = os.path.splitext(file.name)[1] # 拡張子を取得
        if not extension.lower() in settings.VALID_EXTENSIONS:
            raise forms.ValidationError('mp4ファイルを選択してください！')

class ItemAddForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['item_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class HistoryAddForm(forms.ModelForm):

    class Meta:
        model = History
        fields = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # field.widget = forms.HiddenInput()

class ResultAddForm(forms.ModelForm):

    class Meta:
        model = Result
        fields = ['result_class', 'box_x_min', 'box_y_min', 'box_x_max', 'box_y_max']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['result_class'].widget = forms.HiddenInput()
        # self.fields['box_x_min'].widget = forms.HiddenInput()
        # self.fields['box_y_min'].widget = forms.HiddenInput()
        # self.fields['box_x_max'].widget = forms.HiddenInput()
        # self.fields['box_y_max'].widget = forms.HiddenInput()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget = forms.HiddenInput()


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name', 'private']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # デフォルト値をNoneに設定
        super().__init__(*args, **kwargs)
        self.fields['private'].initial = False
        self.fields['private'].widget = forms.HiddenInput()
        self.fields['group_name'].widget.attrs.update({'placeholder': 'グループ名を入力'})
        if user:
            self.fields['user'].initial = user
        

class JoinGroupForm(forms.Form):
    group_id = forms.CharField(
        label='グループID',
        max_length=12,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'グループIDを入力'})
    )




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
