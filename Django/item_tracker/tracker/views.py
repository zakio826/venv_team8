from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import BaseModelForm
from django.shortcuts import redirect

from django.http import HttpResponse

import logging

from django.urls import reverse_lazy
from django.views import generic
from django import forms

# from .forms import InquiryForm, AssetCreateForm, ItemAddForm, ImageAddForm, AssetMultiCreateForm, ItemMultiAddForm, GroupJoinForm, ItemAddEXForm, .
from .forms import *
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
        print("eee", context['form'].initial)
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
        # print("ddd", asset.id)
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
        image = form.save(commit=False)
        image.user = self.request.user
        image.save()
        # ttt = re.findall(r'\d+', self.request.path)
        self.id = image.id
        self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        messages.success(self.request, '写真を登録しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "写真の登録に失敗しました。")
        return super().form_invalid(form)


class ItemAddView(LoginRequiredMixin, generic.CreateView):
    model = Image
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
        images = Image.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)
        context['form'].fields['group'].initial = images.group
        context['form'].fields['asset'].initial = images.asset
        extra = {
            "object": self.object,
            "image": images.image,
        }
        # print(self.success_url)
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.user = self.request.user
        asset.save()
        form_kwargs = self.get_form_kwargs()
        # print("rrr", form_kwargs)
        finish = form_kwargs['data']['finish']
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        if finish == '0':
            print("true")
            self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        else:
            print("false")
            self.success_url = reverse_lazy(f'tracker:history_add', kwargs={'id': self.id})
        messages.success(self.request, 'アイテムを追加しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # print("rrr", form.fields['finish'])
        # print("aaa", form.fields['finish'].initial)
        # print("aaa", form.fields['finish'].choices)
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)

class HistoryAddView(LoginRequiredMixin, generic.CreateView):
    model = Result
    model = Image
    template_name = 'history_add.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    # form_class = forms.inlineformset_factory(Image, History, fields=('user',))
    # form_class = ResultAddForm
    fields = ()
    success_url = reverse_lazy('tracker:asset_list')
    # form_set = forms.formset_factory(
    #     form = form_class,
    #     # formset = ResultAddForm(**self.get_form_kwargs()),
    #     # extra = items.__len__(),
    #     # max_num = items.__len__(),
    # )

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        # print(self.id)
        # print(Asset.objects.get(id=self.id))
        images = Image.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)
        # context['form'].fields['group'].initial = images.group
        # context['form'].fields['asset'].initial = images.asset

        items = Item.objects.filter(asset=images.asset)
        result_add_form = forms.formset_factory(
            form = ResultAddForm,
            # form = self.form_class,
            # formset = ResultAddForm(**self.get_form_kwargs()),
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        # print("dsfsdf", Item.objects.filter(asset=images.asset).__len__())
        # print("dsfsdf", result_add_form)
        # self.form_class = result_add_form
        # print("mm", result_add_form())
        # print("mm", items.__len__())

        # ttttt = [
        #     {
        #         'group': images.group,
        #         'asset': images.asset,
        #         'item': x,
        #         'image': images,
        #         'result_class': 1,
        #     } for x in items
        # ]
        # print("fff0", ttttt[0])
        # print("fff1", ttttt[1])
        # print("fff2", ttttt[2])
        # print("fff3", ttttt[3])
        # result_add_form(
        # )
        # print(result_add_form().instance)
        # print(result_add_form().get_context()['formset'])
        # for form in result_add_form.forms:
        #     print(form.as_table())
        # self.form = result_add_form()
        
        # print("f s", result_add_form().__getitem__(0).fields)
        # for index in range(items.__len__()):
        #     result_add_form().__getitem__(index).fields['group'].initial = images.group
        #     result_add_form().__getitem__(index).fields['asset'].initial = images.asset
        #     result_add_form().__getitem__(index).fields['item'].initial = items[index]
        #     result_add_form().__getitem__(index).fields['image'].initial = images
        #     result_add_form().__getitem__(index).fields['result_class'].initial = 1

        # for index in range(items.__len__()):
        #     print(index, "group", result_add_form().__getitem__(index).fields['group'].initial)
        #     print(index, "asset", result_add_form().__getitem__(index).fields['asset'].initial)
        #     print(index, "item", result_add_form().__getitem__(index).fields['item'].initial)
        #     print(index, "image", result_add_form().__getitem__(index).fields['image'].initial)
        #     print(index, "result_class", result_add_form().__getitem__(index).fields['result_class'].initial)
        #     print()
        # print("fs", result_add_form().management_form)
        
        extra = {
            "object": self.object,
            "image": images.image,
            "items": items,
            "result_add_form": result_add_form(
                initial = [
                    {
                        'group': images.group,
                        'asset': images.asset,
                        'item': x,
                        'image': images,
                        'result_class': 1,
                    } for x in items
                ],
            ),
        }
        # self.form_set = result_add_form(
        #     initial = [
        #         {
        #             'group': images.group,
        #             'asset': images.asset,
        #             'item': x,
        #             'image': images,
        #             'result_class': 1,
        #         } for x in items
        #     ],
        # )
        # print(self.success_url)
        # print(self.get_initial())
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context
    
    # def get_form(self, form_class):

    #     return super().get_form(form_class)

    def form_valid(self, form):
        print("eeeff", self.request.POST)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        image = Image.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)

        history = History(group=image.group, asset=image.asset, user=self.request.user, image=image)
        history.save()
        

        print("eee", form)
        ctx = self.get_context_data()
        items = Item.objects.filter(asset=image.asset)
        ttttt = forms.formset_factory(
            form = ResultAddForm,
            # form = self.form_class,
            # formset = ResultAddForm(**self.get_form_kwargs()),
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        print("fdsf", history.id)
        # history_id = history.objects
        formset = ttttt(self.request.POST, self.request.FILES)
        print("ttt0", formset.forms)
        if formset.is_valid():
            for form in formset.forms:
                result = form.save(commit=False)
                # print("eeet", form)
                result.history = history
                result.save()
            # print("ttt1", self.object)
            # self.object = formset.save(commit=False)
            # self.object.history = history.save()
            # self.object.save()
            # print("ttt2", self.object)

            # # FormSet の内容を保存
            # print("ttt3", formset)
            # formset.instance = self.object
            # formset.save()
            print("ttt4", formset)
            messages.success(self.request, 'アイテムを追加しました。')
            return super().form_valid(form)

            # return redirect(self.get_redirect_url())
        else:
            ctx["form"] = formset
            print("tttd", form)
            return super().form_invalid(form)
            # return self.render_to_response(ctx)
        
        # formset = self.form_set(self.request.POST)
        # if formset.is_valid():
        #     result = formset.save(commit=False)
        #     result.history = history.id
        #     result.save()

        # form_kwargs = self.get_form_kwargs()
        # # print("rrr", form_kwargs)
        # finish = form_kwargs['data']['finish']
        # if finish == '0':
        #     print("true")
        #     self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
        # else:
        #     print("false")
        #     self.success_url = reverse_lazy('tracker:asset_list')
        # print("SSD")
        # messages.success(self.request, 'アイテムを追加しました。')
        # return super().form_valid(form)
    
    def form_invalid(self, form):
        print("eeef", form)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        # image = Image.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)

        # history = History(group=image.group, asset=image.asset, user=self.request.user, image=image)
        # history.save()

        # ctx = self.get_context_data()
        # formset = ctx["result_add_form"]
        # if formset.is_valid():
        #     print("ttt1", self.object)
        #     self.object = form.save(commit=False)
        #     self.object.history = history.id
        #     self.object.save()
        #     print("ttt2", self.object)

        #     # FormSet の内容を保存
        #     print("ttt3", formset)
        #     formset.instance = self.object
        #     formset.save()
        #     print("ttt4", formset)

        #     # return redirect(self.get_redirect_url())
        # else:
        #     ctx["form"] = form
        #     print("tttd", self.object)
            # return self.render_to_response(ctx)
        
        # formset = self.form_set(self.request.POST)
        # if formset.is_valid():
        #     result = formset.save(commit=False)
        #     result.history = history.id
        #     result.save()

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
        context['form'].__getitem__('image_add_form').fields['group'].required = False
        context['form'].__getitem__('image_add_form').fields['asset'].required = False
        context['form'].__getitem__('image_add_form').fields['user'].initial = self.request.user
        context['form'].__getitem__('image_add_form').fields['user'].widget = forms.HiddenInput()
        context['form'].__getitem__('image_add_form').fields['front'].initial = True

        # context['form'].__getitem__('item_add_form').fields['group'].initial = Group.objects.get(id=1)
        # context['form'].__getitem__('item_add_form').fields['asset'].initial = Asset.objects.prefetch_related('group').get(id=44)
        context['form'].__getitem__('item_add_form').fields['group'].required = False
        context['form'].__getitem__('item_add_form').fields['asset'].required = False
        context['form'].__getitem__('item_add_form').fields['item_name'].required = False
        # context['form'].__getitem__('item_add_form').fields['item_name'].initial = "ダミーアイテム"
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
        id_asset = form.__getitem__('asset_create_form').save().id
        asset = Asset.objects.prefetch_related('group').get(id=id_asset)
        group = asset.group

        # self.request.POST['image_add_form-group'] = group
        # self.request.POST['image_add_form-asset'] = str(asset.id)
        # form.__getitem__('image_add_form').save(group=group, asset=asset)
        ImageAddForm.save(group=group, asset=asset)

        # self.request.POST['item_add_form-group'] = group
        # self.request.POST['item_add_form-asset'] = asset
        # for item_name in form.data.__reduce__()[1][2]['item_list']:
        #     self.request.POST['item_add_form-item_name'] = item_name
        #     form.__getitem__('item_add_form').save()
        # form.__getitem__('item_add_form').save(group=group, asset=asset, item_list=form.data.__reduce__()[1][2]['item_list'])
        ItemAddEXForm.save(group=group, asset=asset, item_list=form.data.__reduce__()[1][2]['item_list'])


        # asset = form.__getitem__('asset_create_form').save(commit=False)
        # image = form.__getitem__('image_add_form').save(commit=False)
        # item = form.__getitem__('item_add_form').save(commit=False)
        # # print("04", asset, end="\n\n")
        
        # image.group = asset.group
        # image.asset = asset
        # image()

        # for item_name in form.data.__reduce__()[1][2]['item_list']:
        #     item.group = asset.group
        #     item.asset = asset
        #     item.item_name = item_name
        #     item()

        # asset()
        # form.__getitem__('asset_create_form').save()
        # form.save()
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
        # id_asset = form.__getitem__('asset_create_form').save().id
        # asset = Asset.objects.prefetch_related('group').get(id=id_asset)
        # group = asset.group

        # self.request.POST['image_add_form-group'] = group
        # self.request.POST['image_add_form-asset'] = str(asset.id)
        # form.__getitem__('image_add_form').save(group=group, asset=asset)
        # ImageAddForm.save(group=group, asset=asset)
        # image = form.__getitem__('image_add_form').save(commit=False)
        asset = form.__getitem__('asset_create_form')
        print("ttt1", asset.data['asset_create_form-group'])
        asset.data['asset_create_form-group'] = 0
        print("ttt2", asset.data['asset_create_form-group'])


        image = form.__getitem__('image_add_form')
        print("ttt11", image.data['image_add_form-taken_at'])

        # self.request.POST['item_add_form-group'] = group
        # self.request.POST['item_add_form-asset'] = asset
        # for item_name in form.data.__reduce__()[1][2]['item_list']:
        #     self.request.POST['item_add_form-item_name'] = item_name
        #     form.__getitem__('item_add_form').save()
        # form.__getitem__('item_add_form').save(group=group, asset=asset, item_list=form.data.__reduce__()[1][2]['item_list'])
        # ItemAddEXForm.save(group=group, asset=asset, item_list=form.data.__reduce__()[1][2]['item_list'])
        item = form.__getitem__('item_add_form').save(commit=False)


        # # print("08", form.data.get('item_list'), end="\n\n")
        # form.data.__setitem__('image_add_form-group', self.request.POST['asset_create_form-group'])
        # print("04sss", self.request.POST['image_add_form-group'], end="\n\n")

        # print("04s", self.request.POST, end="\n\n")
        # print("04s1", type(self.request.POST['image_add_form-group']), end="\n\n")
        # print("04s2", type(self.request.POST['image_add_form-asset']), end="\n\n")
        # print("04s3", type(self.request.POST['image_add_form-taken_at']), end="\n\n")

        # group = self.request.POST['image_add_form-group']
        # asset = form.__getitem__('asset_create_form').save().id
        # print("040", asset, end="\n\n")
        # # print("041", type(str(asset.id)), end="\n\n")
        # print("042", group, end="\n\n")

        # self.request.POST['image_add_form-group'] = group
        # self.request.POST['image_add_form-asset'] = str(asset.id)
        # form.__getitem__('image_add_form').save()

        # # image = form.__getitem__('image_add_form').save(commit=False)
        # # print("05", image, end="\n\n")
        # # item = form.__getitem__('item_add_form').save(commit=False)
        # # print("06", item, end="\n\n")

        # # image.group = asset.group
        # # image.asset = asset
        # # image()

        # self.request.POST['item_add_form-group'] = group
        # self.request.POST['item_add_form-asset'] = asset
        # for item_name in form.data.__reduce__()[1][2]['item_list']:
        #     self.request.POST['item_add_form-item_name'] = item_name
        #     form.__getitem__('item_add_form').save()
        # #     item.item_name = item_name
        # #     item()

        # # asset()

        # print("05", form.data.values(), end="\n\n")
        # print("06", form.data['item_list'], end="\n\n")
        # print("07", type(form.data['item_list']), end="\n\n")
        # print("08", form.data.__reduce__(), end="\n\n")
        # print("09", type(form.data.__reduce__()), end="\n\n")
        # print("091", form.data.__reduce__()[1][2]['item_list'], end="\n\n")

        # asset = form.__getitem__('asset_create_form').save(commit=False)
        # print("10", asset, end="\n\n")
        # print("11", asset.group, end="\n\n")
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
    model = Asset
    template_name = 'group_join.html'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    # form = forms.inlineformset_factory(Image, History, fields=('user'))
    # form_class = forms.inlineformset_factory(Image, History, fields=('user'))
    fields = ()
    success_url = reverse_lazy('tracker:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # context['form'].fields['user'].queryset = self.request.user
        # context['form'].fields['group'].queryset = Group.objects.filter(user=self.request.user)
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

        asset_create_form = AssetCreateForm(**self.get_form_kwargs())
        asset_create_form.fields['group'].queryset = groups

        image_add_form = ImageAddForm(**self.get_form_kwargs())
        image_add_form.fields['group'].required = False
        image_add_form.fields['asset'].required = False
        image_add_form.fields['user'].initial = self.request.user
        image_add_form.fields['user'].widget = forms.HiddenInput()
        image_add_form.fields['front'].initial = True

        # item_add_form = ItemAddEXForm(**self.get_form_kwargs())
        item_add_form = forms.formset_factory(
            form = ItemAddEXForm,
        )
        
        context.update({
            "asset_create_form": asset_create_form,
            "image_add_form": image_add_form,
            "item_add_form": item_add_form,
        })
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        print("ttt", form.data, end="\n\n")
        print("ttte", self.object, end="\n\n")
        # asset = AssetCreateForm(**self.get_form_kwargs()).save()
        asset = AssetCreateForm(**self.get_form_kwargs()).data
        print(asset)
        asset = AssetCreateForm(**self.get_form_kwargs()).data
        obj.asset = asset.id
        # obj.asset = asset.id
        obj.save()
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "管理項目の作成に失敗しました。")
        return super().form_invalid(form)