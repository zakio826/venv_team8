from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin

import logging

from django.urls import reverse_lazy
from django.views import generic

from .forms import InquiryForm
# from accounts.models import CustomUser
from django.db import models
from .models import Group, GroupMember, Asset, Item, Image, History, Result

logger = logging.getLogger(__name__)
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from .forms import GroupForm, JoinGroupForm
from django.contrib.auth.decorators import login_required

class IndexView(generic.TemplateView):
    template_name = "index.html"

class InquiryView(generic.FormView):
    template_name = "inquiry.html"
    form_class = InquiryForm
    success_url = reverse_lazy('tracker:inquiry')

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'メッセージを送信しました。')
        logger.info('Inquiry sent by {}'.format(form.cleaned_data['name']))
        return super().form_valid(form)

class AssetListView(LoginRequiredMixin, generic.ListView):
    model = Asset
    template_name = 'asset_list.html'

    def get_queryset(self):
        belong = GroupMember.objects.prefetch_related('group').filter(user=self.request.user)
        images = Image.objects.prefetch_related('group').prefetch_related('asset').filter(front=True)
        for i in belong:
            images = images.filter(group=i.group)
        print(images)
        for i in images:
            print(i.asset)
            print(i.group)
        return images

class AssetDetailView(LoginRequiredMixin, generic.DetailView):
    model = Asset
    template_name = 'asset_detail.html'
    slug_field = "asset_name" # モデルのフィールドの名前
    slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        extra = {
            "object": self.object,
            "image_list": Image.objects.prefetch_related('asset').filter(asset=self.object.id).filter(front=True),
            "item_list": Item.objects.prefetch_related('asset').filter(asset=self.object.id),
        }
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context
    

@login_required
def create_group(request):
    if request.method == 'POST':
        Group.private=False
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']
            
            # 同じグループ名のレコードが存在しないかを確認
            group_exists = Group.objects.filter(user=request.user, group_name=group_name).exists()
            
            if group_exists:
                messages.error(request, 'あなたは同じ名前のグループをすでに作成しています。別の名前を選択してください。')
            else:
                group = form.save(commit=False)
                group.user = request.user  # ユーザーを設定
                group.save()

                # グループを作成したユーザーをグループメンバーとして追加
                GroupMember.objects.create(user=request.user, group=group)

                return redirect('tracker:index')  # グループ一覧ページにリダイレクトする
    else:
        form = GroupForm()

    return render(request, 'create_group.html', {'form': form})


@login_required
def join_group(request):
    if request.method == 'POST':
        form = JoinGroupForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data['group']
            user_already_in_group = GroupMember.objects.filter(user=request.user, group=group).exists()
            
            if user_already_in_group:
                messages.error(request, '既にこのグループに参加しています。')
            else:
                # グループメンバーとしてユーザーを追加
                GroupMember.objects.create(user=request.user, group=group)
                return redirect('tracker:index')  # グループ一覧ページにリダイレクトする
    else:
        form = JoinGroupForm()

    return render(request, 'join_group.html', {'form': form})


def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    return render(request, 'group_detail.html', {'group': group})

@login_required
def mypage(request):
    user_groups = GroupMember.objects.filter(user=request.user)
    return render(request, 'mypage.html', {'user_groups': user_groups})