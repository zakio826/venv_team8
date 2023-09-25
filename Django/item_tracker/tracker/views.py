from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponse

import logging

from django.urls import reverse_lazy
from django.views import generic
from django import forms

from .forms import InquiryForm, AssetCreateForm, ItemAddForm, ImageAddForm, AssetMultiCreateForm, ItemMultiAddForm, GroupJoinForm, ItemAddEXForm
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
        images = None
        if len(belong) >= 1:
            images = Image.objects.prefetch_related('group').prefetch_related('asset').filter(front=True)
            image_list  =[]
            for b in belong:
                print("fff", b.group)
                image_list.append(images.filter(group=b.group))
            print(image_list)
            if len(image_list) <= 0:
                images = None
                pass
            else:
                images = image_list[0]
                for i in image_list:
                    images = images|i
        print(images)
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
        belongs = GroupMember.objects.prefetch_related('group').filter(user=self.request.user)
        group_list = []
        print("ddd", belongs)
        print("ddd", belongs[0])
        for b in belongs:
            print("fff", b.group.id)
            group_list.append(Group.objects.filter(id=b.group.id))
        print(group_list)
        groups = group_list[0]
        if len(group_list) >= 2:
            for g in group_list[1:]:
                groups = groups|g
        print(groups)
        context['form'].fields['group'].queryset = groups
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
        context['form'].fields['user'].widget = forms.HiddenInput()
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
        # print(self.id)
        # print(Asset.objects.get(id=self.id))
        assets = Asset.objects.prefetch_related('group').get(id=self.id)
        context['form'].fields['group'].initial = assets.group
        context['form'].fields['asset'].initial = assets
        return context

    

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        form_kwargs = self.get_form_kwargs()
        # print("rrr", form_kwargs)
        finish = form_kwargs['data']['finish']
        if finish == '0':
            print("true")
            ttt = re.findall(r'\d+', self.request.path)
            self.id = int(ttt[0])
            self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        else:
            print("false")
            self.success_url = reverse_lazy('tracker:asset_list')
        messages.success(self.request, 'アイテムを追加しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # print("rrr", form.fields['finish'])
        # print("aaa", form.fields['finish'].initial)
        # print("aaa", form.fields['finish'].choices)
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)



class AssetMultiCreateView(LoginRequiredMixin, generic.CreateView):
    model = Asset
    template_name = 'asset_multi_create.html'
    form_class = AssetMultiCreateForm
    success_url = reverse_lazy('tracker:asset_list')
    # success_url = reverse_lazy('tracker:item_regist' )

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        kwargs = {'instance': self.request.user}
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # print(context['form'])
        belongs = GroupMember.objects.prefetch_related('group').filter(user=self.request.user)
        group_list = []
        # print("ddd", belongs)
        # print("ddd", belongs[0])
        for b in belongs:
            # print("fff", b.group.id)
            group_list.append(Group.objects.filter(id=b.group.id))
        # print(group_list)
        groups = group_list[0]
        if len(group_list) >= 2:
            for g in group_list[1:]:
                groups = groups|g
        # print(groups)

        print("01", context, end="\n\n")
        print("02", context['view'].form_class, end="\n\n")
        print("03", context['form'].__getitem__('asset_create_form').fields, end="\n\n")

        context['form'].__getitem__('asset_create_form').fields['group'].queryset = groups

        # context['form'].__getitem__('image_add_form').fields['group'].initial = Group.objects.get(id=1)
        # context['form'].__getitem__('image_add_form').fields['asset'].initial = Asset.objects.prefetch_related('group').get(id=44)
        context['form'].__getitem__('image_add_form').fields['user'].initial = self.request.user
        context['form'].__getitem__('image_add_form').fields['user'].widget = forms.HiddenInput()

        # context['form'].__getitem__('item_add_form').fields['group'].initial = Group.objects.get(id=1)
        # context['form'].__getitem__('item_add_form').fields['asset'].initial = Asset.objects.prefetch_related('group').get(id=44)
        context['form'].__getitem__('item_add_form').fields['item_name'].initial = "ダミーアイテム"
        context['form'].__getitem__('item_add_form').fields['group'].widget = forms.HiddenInput()
        context['form'].__getitem__('item_add_form').fields['asset'].widget = forms.HiddenInput()
        context['form'].__getitem__('item_add_form').fields['item_name'].widget = forms.HiddenInput()

        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        extra = {
            "object": self.object,
        }
        # print(self.success_url)
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context

    def form_valid(self, form):
        asset = form.__getitem__('asset_create_form').save(commit=False)
        form.__getitem__('image_add_form').save(commit=False).group = asset.group
        form.__getitem__('image_add_form').save(commit=False).asset = asset

        for item_name in form.data['item_list']:
            form.__getitem__('item_add_form').save(commit=False).group = asset.group
            form.__getitem__('item_add_form').save(commit=False).asset = asset
            form.__getitem__('item_add_form').save(commit=False).item_name = item_name
            form.__getitem__('item_add_form').save()

        form.save()
        # asset = form.save(commit=False)
        # print("04", form, end="\n\n")
        # print("05", form.__getitem__('asset_create_form').fields, end="\n\n")
        # print("06", asset, end="\n\n")
        # print("07", form.__getitem__('asset_create_form').save(commit=False).group, end="\n\n")
        # is_valid
        # asset.user = self.request.user
        # asset.save()
        # print("ddd", asset.id)
        self.success_url = reverse_lazy(f'tracker:asset_multi_create')
        # self.success_url = reverse_lazy(f'tracker:image_add', kwargs={'id': asset.id})
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # print("04", form, end="\n\n")
        print("05", form.data.values(), end="\n\n")
        print("06", form.data['item_list'], end="\n\n")
        print("07", type(form.data['item_list']), end="\n\n")
        print("08", form.data.__reduce__(), end="\n\n")
        print("09", type(form.data.__reduce__()), end="\n\n")
        # print("06", forms.formset_factory(self.request.POST), end="\n\n")
        # print("06", form.data['item_list'], end="\n\n")
        # for name in form.data['item_list']:
        #     print("07", name, end="\n")
        # print("08", form.data.get('item_list'), end="\n\n")
        # print("09", self.request.POST, end="\n\n")
        # print("10", self.request.POST['item_list'], end="\n\n")
        # print("11", self.request.POST.get('item_list'), end="\n\n")
        # print("12", form.data.get('item_list'), end="\n\n")

        messages.error(self.request, "管理項目の作成に失敗しました。")
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