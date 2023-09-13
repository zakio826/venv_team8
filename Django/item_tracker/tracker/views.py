from django.contrib.auth.mixins import LoginRequiredMixin

import logging

from django.urls import reverse_lazy
from django.views import generic

from .forms import InquiryForm
from .models import Group, Asset, Item, Image, History, Result

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
    
class AssetListView(generic.TemplateView):
    template_name = 'asset_list.html'


class AssetListsView(LoginRequiredMixin, generic.ListView):
    model = Asset
    template_name = 'asset_list.html'

    def get_queryset(self):
        assets = Asset.objects.filter(group=self.request.group)
        return assets