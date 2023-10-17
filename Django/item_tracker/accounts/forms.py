from typing import Any
from allauth.account.forms import (
    SignupForm,
    LoginForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    ChangePasswordForm,
    AddEmailForm,
    SetPasswordForm, 
)

from betterforms.multiform import MultiForm

from django import forms
from tracker.models import Group, GroupMember



class SignupGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['user', 'group_name', 'private']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group_name'].initial = '個人利用グループ'
        self.fields['private'].initial = True

        for field in self.fields.values():
            field.widget.widget = forms.HiddenInput()
            field.widget.attrs['class'] = 'form-control'

    def save(self, user):
        obj = super.save(commit=False)
        obj.user = user
        obj.save()
        return obj


class SignupGroupMemberForm(forms.ModelForm):
    class Meta:
        model = GroupMember
        fields = ['user', 'group']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.widget = forms.HiddenInput()
            field.widget.attrs['class'] = 'form-control'
    
    def save(self, user, group):
        obj = super.save(commit=False)
        obj.user = user
        obj.group = group
        obj.save()
        return obj



#allauthのsignupフォーム上書き
class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            print("qqqqq", field)
            field.widget.attrs['class'] = 'form-control'






#allauthのログインフォーム上書き
class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            print("qqqqq", field)
            field.widget.attrs['class'] = 'form-control'

#allauthのパスワードリセットのメールフォーム上書き
class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

#allauthのnewパスワードフォーム上書き
class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

#allauthのパスワード変更フォーム上書き
class CustomChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

#allauthのメール設定フォーム上書き
class CustomAddEmailForm(AddEmailForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

#allauthのパスワード設定フォーム
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


