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
    model = Image
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
    model = Image
    template_name = 'asset_detail.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset" # モデルのフィールドの名前
    # slug_url_kwarg = "asset" # urls.pyでのキーワードの名前

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        extra = {
            self.object,
            Item.objects.prefetch_related('asset').filter(asset=self.object.asset),
        }
        # コンテキスト情報のキーを追加
        context.update()
        # print(extra)
        print()
        print("ss", self.object)
        print()
        print("aaa", extra)
        print()
        for i in self.get_queryset(context):
            print()
            print(i)
            # print(i.object)
            # print(i.item_list)
        return context
    
    def get_queryset(self, context):
        return Item.objects.prefetch_related('asset').filter(asset=context)