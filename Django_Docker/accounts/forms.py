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


from django import forms


#allauthのsignupフォーム上書き
class CustomSignupForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.move_to_end('username', last=False)
        print(type(self.fields))
        print(self.fields.keys())
        for field in self.fields.values():
            print("qqqqq", field)
            # field.widget.attrs['class'] = 'form-control'


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


