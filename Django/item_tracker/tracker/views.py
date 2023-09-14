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
    
class AssetListsView(generic.TemplateView):
    template_name = 'asset_list.html'


class AssetListView(LoginRequiredMixin, generic.ListView):
    model = GroupMember, Asset, Image, Group
    template_name = 'asset_list.html'

    def get_queryset(self):
        belong = GroupMember.objects.prefetch_related('group').filter(member=self.request.user)
        assets = Asset.objects.all()
        for i in belong:
            assets = assets.filter(group=i.group)
        return assets