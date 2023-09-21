from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponse

import logging

from django.urls import reverse_lazy
from django.views import generic
from django.forms import Form, ModelForm, HiddenInput

from .forms import InquiryForm, AssetCreateForm, ItemAddForm, ImageAddForm, ItemMultiAddForm, GroupJoinForm
from accounts.models import CustomUser
from django.db import models
from .models import Group, GroupMember, Asset, Item, Image, History, Result

logger = logging.getLogger(__name__)
from django.contrib import messages

import re

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
            print("fff", i.group)
            images = images.filter(group=i.group)
        print(images)
        for i in images:
            print(i.asset)
            print(i.group)
        return images

class AssetDetailView(LoginRequiredMixin, generic.DetailView):
    model = Asset
    template_name = 'asset_detail.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前

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
    # success_url = reverse_lazy('tracker:item_regist' )

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        kwargs = {'instance': self.request.user}
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # print(context['form'])
        context['form'].fields['group'].queryset = Group.objects.filter(user=self.request.user)
        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        extra = {
            "object": self.object,
        }
        # print(self.success_url)
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        print("ddd", asset.id)
        self.success_url = reverse_lazy(f'tracker:image_add', kwargs={'id': asset.id})
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "管理項目の作成に失敗しました。")
        return super().form_invalid(form)
    

class ImageAddView(LoginRequiredMixin, generic.CreateView):
    model = Asset
    template_name = 'image_add.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    form_class = ImageAddForm
    success_url = reverse_lazy('tracker:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # print("aaa", self.get_success_url())
        print(self.request.path)
        print(re.findall(r'\d+', self.request.path))
        # print(self.get_slug_field())
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        print(self.id)
        print(Asset.objects.get(id=self.id))
        assets = Asset.objects.prefetch_related('group').get(id=self.id)
        print(assets.group)
        context['form'].fields['group'].initial = assets.group
        context['form'].fields['asset'].initial = assets
        context['form'].fields['user'].initial = self.request.user
        context['form'].fields['user'].widget = HiddenInput()
        context['form'].fields['front'].initial = True

        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        extra = {
            "object": self.object,
        }
        # print(self.success_url)
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        messages.success(self.request, '写真を登録しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "写真の登録に失敗しました。")
        return super().form_invalid(form)

class ItemAddView(LoginRequiredMixin, generic.CreateView):
    model = Asset
    template_name = 'item_add.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    form_class = ItemAddForm
    success_url = reverse_lazy('tracker:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        print(self.id)
        print(Asset.objects.get(id=self.id))
        assets = Asset.objects.prefetch_related('group').get(id=self.id)
        context['form'].fields['group'].initial = assets.group
        context['form'].fields['asset'].initial = assets
        return context

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        # print("aaa")
        # print("asd", form.fields)
        # print("asdfsda", form.fields['finish'].initial)
        if form.fields['finish'].initial == "True":
            ttt = re.findall(r'\d+', self.request.path)
            self.id = int(ttt[0])
            self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        # ttt = re.findall(r'\d+', self.request.path)
        # self.id = int(ttt[0])
        # self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        messages.success(self.request, 'アイテムを追加しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)













class GroupJoinView(LoginRequiredMixin, generic.CreateView):
    model = Group
    template_name = 'group_join.html'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    form_class = GroupJoinForm
    success_url = reverse_lazy('tracker:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        context['form'].fields['group'].queryset = Group.objects.filter(user=self.request.user)
        # print(context['form'])
        # print()
        # # print(AssetCreateForm)
        # print()
        # print(AssetMultiCreateForm.form_classes)
        # print()
        # print(AssetMultiCreateForm.form_classes['asset_create_form'])
        # print()
        # print(AssetMultiCreateForm.form_classes['asset_create_form'])
        # print()
        # print(context['form'].form_classes['asset_create_form'])
        # print()
        # print(context['form'].fields['group'])
        # context['form'].fields['group'].queryset = Group.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "管理項目の作成に失敗しました。")
        return super().form_invalid(form)