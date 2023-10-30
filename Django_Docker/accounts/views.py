from django.shortcuts import render

# Create your views here.
from allauth.account.views import LoginView as AllauthLoginView
from django.shortcuts import redirect
from toolkeeper_app.models import Group, GroupMember
from django.contrib.auth import login
from django.contrib import messages

from django.conf import settings

import secrets
import string


class LoginView(AllauthLoginView):
    def form_valid(self, form):
        personal_use = self.request.POST.get("personal_use") == "on"

        # 通常のログイン処理を実行
        response = super(LoginView, self).form_valid(form)

        # ユーザーがログインした後、ユーザーが正しく設定されていることを確認
        if self.request.user.is_authenticated:
            # ユーザーが個人利用を選択した場合
            if personal_use:
                # グループIDの自動生成と重複チェック
                group_id = self.generate_unique_group_id()
                
                # グループ名を設定
                group_name = "個人利用グループ"

                # 同じホストユーザーとグループ名のグループが存在するかを確認
                group_exists = Group.objects.filter(user=self.request.user, group_name=group_name).exists()

                if group_exists:
                    return redirect(settings.LOGIN_REDIRECT_URL)
                else:
                    # グループを作成
                    group = Group.objects.create(
                        user=self.request.user,
                        group_name=group_name,
                        private=True,
                        group_id=group_id  # グループIDを設定
                    )
                    # ユーザーをグループメンバーとして追加
                    GroupMember.objects.create(user=self.request.user, group=group)
                    return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                # ユーザーがどのグループにも所属していないかを確認
                user_belongs_to_groups = GroupMember.objects.filter(user=self.request.user).exists()
                if user_belongs_to_groups:
                    return redirect(settings.LOGIN_REDIRECT_URL) 
                else:
                    return redirect(settings.LOGIN_REDIRECT_URL)
        return response

    def generate_unique_group_id(self):
        while True:
            group_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            if not Group.objects.filter(group_id=group_id).exists():
                return group_id

