from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin

import logging

from django.urls import reverse_lazy
from django.views import generic
from django.forms import Form

from .forms import InquiryForm, AssetCreateForm
from accounts.models import CustomUser
from django.db import models
from .models import Group, GroupMember, Asset, Item, Image, History, Result

logger = logging.getLogger(__name__)
from django.contrib import messages

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
    
# from django import http

class AssetCreateView(LoginRequiredMixin, generic.CreateView):
    model = Asset
    template_name = 'asset_create.html'
    form_class = AssetCreateForm
    success_url = reverse_lazy('tracker:asset_list')
    # form = AssetCreateForm(user=http.request)

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        context['form'].fields['group'].queryset = Group.objects.filter(user=self.request.user)
        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        # extra = {
        #     "asset_name": context['form'].fields.queryset = Group.objects.filter(user=user),
        #     "group": Group.objects.filter(user=self.request.user)
        # }
        # print(context['form'].fields)
        # print(extra['object'])
        # print(extra['group'])
        # # コンテキスト情報のキーを追加
        # context.update(extra)
        return context
    
    # def get_form(self):
    #     if self.request.method == 'POST':
    #         form = AssetCreateForm(user=self.request.user, data=self.request.POST)
            # if form.is_valid():
            #     asset = form.save(commit=False)
            #     asset.user = self.request.user
            #     asset.save()
            #     messages.success(self.request, '管理項目を作成しました。')
            #     return super().form_valid(form)

    def form_valid(self, form):
        # form = AssetCreateForm(user=self.request.user, data=self.request.POST)
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "管理項目の作成に失敗しました。")
        return super().form_invalid(form)