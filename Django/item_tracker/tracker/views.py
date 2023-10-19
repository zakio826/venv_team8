from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import BaseModelForm
from django.shortcuts import redirect
from django.conf import settings

from django.http import HttpResponse, QueryDict, JsonResponse
import logging

from django.urls import reverse_lazy
from django.views import generic
from django import forms


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
# from .forms import InquiryForm, AssetCreateForm, ItemAddForm, ImageAddForm, AssetMultiCreateForm, ItemMultiAddForm, GroupJoinForm, ItemAddEXForm, .
from .forms import *
from accounts.models import CustomUser
from django.db import models
from .models import Group, GroupMember, Asset, Item, Image, History, Result

logger = logging.getLogger(__name__)
from django.contrib import messages

import re

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials


from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client import file, client, tools
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.http import MediaIoBaseDownload
import shutil

from ultralytics import YOLO


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
            image_list = []
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
        print()
        # print(0.855967)
        # print(round(0.8559670781893004, 6))
        # print()
        # print("images[1].image.path", images[1].movie.path)
        # print()
        return images

class AssetDetailView(LoginRequiredMixin, generic.DetailView):
    model = Asset
    template_name = 'asset_detail.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前


    def download_file(self, file_id, file_name):
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = open(os.path.join(settings.MEDIA_ROOT, 'learning', file_name), 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while done is False:
            status, done = downloader.next_chunk()
            print(f'Download {file_name} {int(status.progress() * 100)}%')

        # self.asset.learning_model = os.path.join(settings.MEDIA_ROOT, 'learning', self.pt_file_name)
        self.asset.learning_model.name = os.path.join('learning', self.pt_file_name)
        self.asset.save()

    #Drive上のサブディレクトリの中身を参照しフォルダごとダウンロード(条件あり)
    def download_folder(self, folder_id, target_folder_name):
        query = f"'{folder_id}' in parents"
        results = self.drive_service.files().list(q=query).execute()
        files = results.get('files', [])
    
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                subfolder_id = file['id']
                subfolder_name = file['name']
                subfolder_path = os.path.join(os.path.join(os.path.join(settings.MEDIA_ROOT, 'learning'), target_folder_name), subfolder_name)
                os.makedirs(subfolder_path, exist_ok=True)
                self.download_folder(subfolder_id, target_folder_name)
            else:
                file_id = file['id']
                file_name = file['name']
                # ext = os.path.splitext(file_name)[1]
                # self.pt_file_name = self.file_name + '.pt'
                if file_name == self.pt_file_name:
                    # return os.path.splitext(file_name)[0]
                    self.download_file(file_id, file_name)

    # .ptファイルの名前を取得し、ローカル上で作成されるフォルダ名に使用
    def get_pt_folder_name(self):
        # query_list = [
        #     f"'{settings.GOOGLE_DRIVE_FOLDER_ID}' in parents",
        #     "mimeType = 'application/vnd.pt'"
        #     # "(name contains '.pt')"
        # ]
        # query = " and ".join(query_list)
        query = f"'{self.asset.drive_folder_id}' in parents"
        results = self.drive_service.files().list(q=query).execute()
        # folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        # query = f"'{folder_id}' in parents and mimeType = 'application/vnd.pt'"
        # query = query = f"'{folder_id}' in parents and mimeType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'"
        # results = self.drive_service.files().list(
        #     q = query,
        #     fields = "files(id, name)",
        #     # fields = "nextPageToken, files(id, name)",
        #     # pageSize = 100,
        # ).execute()
        files = results.get('files', [])

        for file in files:
            file_name = file['name']
            ext = os.path.splitext(file_name)[1]
            if ext == '.pt':
                return os.path.splitext(file_name)[0]

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        self.asset = Asset.objects.get(id=self.object.id)
        self.historys = History.objects.prefetch_related('image').filter(asset=self.asset).order_by('-updated_at')
        self.pt_file_name = os.path.splitext(self.historys[0].image.movie.name[6:])[0] + '.pt'
        
        if self.asset.drive_folder_id:
            service_account_key_path = os.path.join(settings.MEDIA_ROOT, settings.SERVICE_ACCOUNT_KEY_NAME)
            creds = service_account.Credentials.from_service_account_file(
                service_account_key_path, # サービスアカウントキーのJSONファイルへのパス
                scopes = settings.GOOGLE_DRIVE_API_SCOPES, # Google Drive APIのスコープ
            )
            # http_auth = creds.authorize(Http())
            # self.drive_service = build('drive', 'v3', http=http_auth)
            self.drive_service = build('drive', 'v3', credentials=creds)

            # .pt フォルダ名を取得
            pt_folder_name = self.get_pt_folder_name()

            # ダウンロード
            if pt_folder_name:
                self.download_folder(self.asset.drive_folder_id, pt_folder_name)
            #     # 特定の単語が含まれるフォルダを削除 8
            #     delete_folders_with_keywords(DOWNLOAD_DIR, ["json", "motion", "tex","trace"])
                
            else:
                print("ptファイルがないか処理の途中でエラーが発生しています。")

        # print("self.asset.learning_model.name:", self.asset.learning_model.name)
        # print("self.asset.learning_model.path:", self.asset.learning_model.path)
        extra = {
            "object": self.object,
            "image_list": Image.objects.prefetch_related('asset').filter(asset=self.object.id).filter(front=True),
            "item_list": Item.objects.prefetch_related('asset').filter(asset=self.object.id, outer_edge=False),
            "asset_id": self.object.id,
            "historys": History.objects.prefetch_related('asset').prefetch_related('user').filter(asset_id=self.object.id),
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
        # asset.user = self.request.user
        asset.save()
        # print("ddd", asset.id)
        self.success_url = reverse_lazy(f'tracker:image_add', kwargs={'id': asset.id})
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "管理項目の作成に失敗しました。")
        return super().form_invalid(form)
    

def chengeLabel(w_size, h_size, classNum, w_min, h_min, w_max, h_max):
    """ラベル情報の出力 (YOLO)
    """
    # バウンディングボックスの座標を正規化座標に変換
    x_min = float(w_min) / float(w_size)
    y_min = float(h_min) / float(h_size)
    x_max = float(w_max) / float(w_size)
    y_max = float(h_max) / float(h_size)

    # バウンディングボックスの中心座標とサイズを計算
    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    box_width  = x_max - x_min
    box_height = y_max - y_min

    label = [str(classNum), str(x_center), str(y_center), str(box_width), str(box_height)]
    return label

def chengeBox(w_size, h_size, label):
    """ラベル情報からバウンディングボックスを出力 (YOLO)
    """
    # バウンディングボックスの中心座標とサイズから頂点座標を算出
    x_center   = float(label[1]) * 2.0
    y_center   = float(label[2]) * 2.0
    box_width  = float(label[3])
    box_height = float(label[4])

    x_max = (x_center + box_width) / 2.0
    x_min = x_center - x_max
    y_max = (y_center + box_height) / 2.0
    y_min = y_center - y_max

    # バウンディングボックスの座標をピクセルに変換
    w_min = x_min * float(w_size)
    h_min = y_min * float(h_size)
    w_max = x_max * float(w_size)
    h_max = y_max * float(h_size)

    Bounding_box = [int(label[0]), round(w_min, 6), round(h_min, 6), round(w_max, 6), round(h_max, 6)]
    return Bounding_box

class ImageAddView(LoginRequiredMixin, generic.CreateView):
    model = Image
    template_name = 'image_add.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    # form_class = ImageAddForm
    fields = ()
    item_add_form = ItemAddForm
    image_add_form = ImageAddForm
    history_add_form = HistoryAddForm
    result_add_form = ResultAddForm
    success_url = reverse_lazy('tracker:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        # print("aaa", self.get_success_url())
        print(self.request.path)
        # print(re.findall(r'\d+', self.request.path))
        # print(self.get_slug_field())
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])

        image_add_form = self.image_add_form(**self.get_form_kwargs())
        history_add_form = self.history_add_form(**self.get_form_kwargs())
        result_add_form = self.result_add_form(**self.get_form_kwargs())
        item_add_form = None

        # print(image_add_form['group'])
        # print(Asset.objects.get(id=self.id))

        assets = Asset.objects.prefetch_related('group').get(id=self.id)

        # print(assets.group)

        # image_add_form['group'].initial = assets.group
        # image_add_form['asset'].initial = assets
        image_add_form['user'].initial = self.request.user

        history_add_form['user'].initial = self.request.user
        history_add_form['user'].field.widget = forms.HiddenInput()


        # result_add_form['asset'].initial = assets
        result_add_form['result_class'].initial = 9
        # result_add_form['asset'].field.widget = forms.HiddenInput()
        # result_add_form['item'].field.widget = forms.HiddenInput()
        # result_add_form['image'].field.widget = forms.HiddenInput()
        result_add_form['result_class'].field.widget = forms.HiddenInput()
        
        ttts = re.findall(r'[^0-9]+', self.request.path)
        print("ff", ttts)
        if ttts[0] == '/asset-create/image-add/':
            image_add_form['user'].field.widget = forms.HiddenInput()
            # image_add_form['front'].initial = True
            
            item_add_form = self.item_add_form(**self.get_form_kwargs())
            # item_add_form['group'].initial = assets.group
            # item_add_form['asset'].initial = assets
            item_add_form['item_name'].initial = f"外枠"
            item_add_form['item_name'].field.widget = forms.HiddenInput()
            # item_add_form['finish'].field.widget = forms.HiddenInput()
            # item_add_form['outer_edge'].initial = True

            submit = "登録"
        else:
            members = GroupMember.objects.prefetch_related('group').prefetch_related('user')
            # users = CustomUser.objects.prefetch_related('group').prefetch_related('user')
            # context['form'].fields['user'].initial = users.get(user=self.request.user)
            user_li = []
            for m in members.filter(group=assets.group):
                user_li.append(CustomUser.objects.filter(id=m.user.id))
            users = user_li[0]
            if len(user_li) >= 2:
                for u in user_li[1:]:
                    users = users|u
            print("uu", users)
            image_add_form['user'].field.queryset = users
            submit = "追加"

        # 追加したいコンテキスト情報(取得したコンテキスト情報のキーのリストを設定)
        extra = {
            "submit": submit,
            "object": self.object,
            "image_add_form": image_add_form,
            "item_add_form": item_add_form,
            "result_add_form": result_add_form,
        }
        # print(self.success_url)
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context
    

    def form_valid(self, form):
        print("ss", form.data)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        ttts = re.findall(r'[^0-9]+', self.request.path)

        asset = Asset.objects.prefetch_related('group').get(id=self.id)
        image_form = self.image_add_form(self.request.POST, self.request.FILES)
        image_form = image_form.save(commit=False)
        # image_form = form.save(commit=False)
        image_form.group = asset.group
        image_form.asset = asset
        image_form.user = self.request.user
        if ttts[0] == '/asset-create/image-add/':
            image_form.front = True
        image_form.save()

        image = Image.objects.get(id=image_form.id)
        # print(image_form.id)
        # image = image_form.instance
        # print()
        # print("image.image.width: ", type(image.image.width))
        # print("image.image.height:", type(image.image.height))
        # print()
        # print(' '.join(self.chengeLabel(
        #             w_size = image.image.width,
        #             h_size = image.image.height,
        #             classNum = 0,
        #             w_min = form.data['box_x_min'],
        #             h_min = form.data['box_y_min'],
        #             w_max = form.data['box_x_max'],
        #             h_max = form.data['box_y_max']
        #     ))
        # )
        # print()

        
        if ttts[0] == '/asset-create/image-add/':
            item_form = self.item_add_form(self.request.POST)
            item_form = item_form.save(commit=False)
            # item_form.group = asset.group
            item_form.asset = asset
            item_form.outer_edge = True
            item_form.save()
            # item = item_form.instance
        #     image = image.filter(front=True).get(asset=asset)
        # else:
        #     image = image.filter(front=False).filter(asset=asset)[0]
            # item = History.objects.prefetch_related('item').order_by('-updated_at').first()
        item = Item.objects.filter(outer_edge=True).get(asset=asset)

        
        # history = History(group=asset.group, asset=asset, user=self.request.user, image=form.instance)
        history = self.history_add_form(self.request.POST)
        history = history.save(commit=False)
        history.group = asset.group
        history.asset = asset
        history.user = self.request.user
        history.image = image
        history.save()

        coordinate_path = os.path.join(settings.MEDIA_ROOT, history.coordinate.name)
        history_coordinate = open(coordinate_path, 'w')
        history_coordinate.write(
            ' '.join(chengeLabel(
                    w_size = image.image.width,
                    h_size = image.image.height,
                    classNum = 0,
                    w_min = form.data['box_x_min'],
                    h_min = form.data['box_y_min'],
                    w_max = form.data['box_x_max'],
                    h_max = form.data['box_y_max']
            ))
        )
        history_coordinate.close()
        
        # print("ff", form.data['box_x_min'])
        # print("ff", type(form.data['box_x_min']))
        # print("ff", float(form.data['box_x_min']))
        # print("ff", type(float(form.data['box_x_min'])))

        result = self.result_add_form(self.request.POST).save(commit=False)
        result.history = history
        result.item = item
        result.result_class = 9
        result.save()

        # result = Result(
        #     history=history,
        #     asset=asset,
        #     image=image,
        #     item=item,
        #     result_class = int(form.data['result_class']),
        #     box_x_min = float(form.data['box_x_min']),
        #     box_y_min = float(form.data['box_y_min']),
        #     box_x_max = float(form.data['box_x_max']),
        #     box_y_max = float(form.data['box_y_max']),
        # )
        # result.save()
        # print("ff", result.)


        # image = form.save(commit=False)
        # image.user = self.request.user
        # ttt = re.findall(r'\d+', self.request.path)
        print("f", ttts)
        # self.id = int(ttt[0])
        self.id = history.id
        if ttts[0] == '/asset-create/image-add/':
            self.success_url = reverse_lazy(f'tracker:item_add', kwargs={'id': self.id})
            messages.success(self.request, '写真を登録しました。')
        else:
            self.success_url = reverse_lazy(f'tracker:asset_check', kwargs={'id': self.id})
            messages.success(self.request, '写真を追加しました。')
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(self.request, "写真の登録に失敗しました。")
        return super().form_invalid(form)


class ItemAddView(LoginRequiredMixin, generic.CreateView):
    model = Item
    template_name = 'item_add.html'
    pk_url_kwarg = 'id'
    # slug_field = "asset_name" # モデルのフィールドの名前
    # slug_url_kwarg = "asset_name" # urls.pyでのキーワードの名前
    success_url = reverse_lazy('tracker:asset_list')
    formset = forms.formset_factory(
        form = ItemAddForm,
        # extra = 1,
        # max_num = items.__len__(),
    )
    # form_class = ItemAddForm
    fields = ()
    # form_class = formset

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)

        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        history = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').get(id=self.id)
        result = Result.objects.get(history=history)

        extra = {
            "object": self.object,
            "image": history.image.image,
            "box_x_min": result.box_x_min,
            "box_y_min": result.box_y_min,
            "box_x_max": result.box_x_max,
            "box_y_max": result.box_y_max,
            "formset": self.formset,
        }
        # print(self.success_url)
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context

    def form_valid(self, form):
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        history = History.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)

        formset = self.formset(self.request.POST)

        if formset.is_valid():
            for forms in formset:
                print(forms.data)
                item = forms.save(commit=False)
                # item.group = history.group
                item.asset = history.asset
                item.save()

            self.success_url = reverse_lazy(f'tracker:history_add', kwargs={'id': self.id})
            messages.success(self.request, 'アイテムを追加しました。')
            return redirect(self.success_url)

        else:
            messages.error(self.request, "アイテムの追加に失敗しました。")
            return super().form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)

class HistoryAddView(LoginRequiredMixin, generic.CreateView):
    model = Image
    template_name = 'history_add.html'
    pk_url_kwarg = 'id'
    fields = ()
    success_url = reverse_lazy('tracker:asset_list')

    def model_check(self, asset, image):
        
        output_path = os.path.join(settings.MEDIA_ROOT, 'model_check', asset.learning_model.name[8:-3])
        os.makedirs(output_path, exist_ok=True)

        # YOLOモデルの読み込み
        model = YOLO(os.path.join(settings.MEDIA_ROOT, asset.learning_model.name))

        # 物体検出の実行
        results1 = model.predict(source=os.path.join(settings.MEDIA_ROOT, image.image.name), conf=0.50)

        classDict = results1[0].names
        classNums = results1[0].boxes.cls.__array__().tolist()
        confs = results1[0].boxes.conf.__array__().tolist()
        boxes = results1[0].boxes.xyxy.__array__().tolist()

        print()
        for i in range(len(results1[0].boxes.cls)):
            if round(classNums[i]) and self.box[round(classNums[i])]['conf'] < confs[i]:
                self.box[round(classNums[i])]['box_x_min'] = boxes[i][0]
                self.box[round(classNums[i])]['box_y_min'] = boxes[i][1]
                self.box[round(classNums[i])]['box_x_max'] = boxes[i][2]
                self.box[round(classNums[i])]['box_y_max'] = boxes[i][3]
                self.box[round(classNums[i])]['conf'] = confs[i]

            # print(f"{round(classNums[i])}:", classDict[classNums[i]])
            # print(f"  x_min = {boxes[i][0]:>20} px")
            # print(f"  y_min = {boxes[i][1]:>20} px")
            # print(f"  x_max = {boxes[i][2]:>20} px")
            # print(f"  y_max = {boxes[i][3]:>20} px")
            # print(f"  conf  = {confs[i]:>20} %")
        # print("len", len(results1[0].boxes.cls))
        # print()

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        historys = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').order_by('-updated_at')
        history = historys.get(id=self.id)
        print(historys[0].id)
        # last_history = historys.get(id)
        results = Result.objects.filter(history=historys[0])
        # results = Result.objects.prefetch_related('history').filter(asset=history.asset)
        # result = results.filter(history=history)

        items = Item.objects.filter(asset=history.asset, outer_edge=False)
        result_add_form = forms.formset_factory(
            form = ResultAddForm,
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        
        ttts = re.findall(r'[^0-9]+', self.request.path)
        print("f", ttts)
        # self.id = int(ttt[0])
        result = Result.objects.prefetch_related('history').filter(history=history).get(result_class=9)
        self.box = [{
            "box_x_min": result.box_x_min,
            "box_y_min": result.box_y_min,
            "box_x_max": result.box_x_max,
            "box_y_max": result.box_y_max,
            "model_check": False,
        }]
        if ttts[0] == '/asset-check/':
            result_class = 0

            result_history = historys.get(id=result.history.id)
            box_x_fix = (result.box_x_max - result.box_x_min) / result_history.image.image.width
            box_y_fix = (result.box_y_max - result.box_y_min) / result_history.image.image.height

            results = Result.objects.filter(history=History.objects.filter(asset=history.asset).order_by('checked_at')[0])#.exclude(result_class=9)
            for i, r in enumerate(results):
                result_history = historys.get(id=r.history.id)
                if not i:
                    item_x_fix = (r.box_x_max - r.box_x_min) / result_history.image.image.width
                    item_y_fix = (r.box_y_max - r.box_y_min) / result_history.image.image.height
                    item_x_min = r.box_x_min
                    item_y_min = r.box_y_min
                else:
                    item_x_fit = box_x_fix / item_x_fix
                    item_y_fit = box_y_fix / item_y_fix
                    self.box.append({
                        "box_x_min": ((r.box_x_min - item_x_min) * item_x_fit) + result.box_x_min,
                        "box_y_min": ((r.box_y_min - item_y_min) * item_y_fit) + result.box_y_min,
                        "box_x_max": ((r.box_x_max - item_x_min) * item_x_fit) + result.box_x_min,
                        "box_y_max": ((r.box_y_max - item_y_min) * item_y_fit) + result.box_y_min,
                        "conf": 0,
                    })
            
            if history.asset.learning_model:
                # self.box = []
                # for i in Item.objects.filter(history=history):
                #     self.box
                self.box[0]['model_check'] = True
                print()
                self.model_check(history.asset, history.image)
        else:
            result_class = 1
            # results = Result.objects.filter(history=historys[0])
        

        extra = {
            "create": result_class,
            "image": history.image.image,
            "items": items.order_by('-id'),
            "results": self.box,
            # "box_x_min": round(result.box_x_min),
            # "box_y_min": round(result.box_y_min),
            # "box_x_max": round(result.box_x_max),
            # "box_y_max": round(result.box_y_max),
            "result_add_form": result_add_form(
                initial = [
                    {
                        'asset': history.asset,
                        'item': x,
                        'image': history.image,
                        'result_class': result_class,
                    } for x in items
                ],
            ),
        }
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context
    

    def form_valid(self, form):
        print("eeeff", self.request.POST)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        history = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').get(id=self.id)
        

        # image = Image.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)
        
        print("eee", form.data)
        ctx = self.get_context_data()
        items = Item.objects.filter(asset=history.asset, outer_edge=False)
        ttttt = forms.formset_factory(
            form = ResultAddForm,
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        print("fdsf", history.id)
        # history_id = history.objects
        print("fdsf", self.request.FILES)
        formset = ttttt(self.request.POST)
        print("ttt0", formset.forms)
        if formset.is_valid():
            coordinate_path = os.path.join(settings.MEDIA_ROOT, history.coordinate.name)
            history_coordinate = open(coordinate_path, 'a')
            labelList = []
            for i, form in enumerate(formset.forms):

                result = form.save(commit=False)
                # print("eeet", form)
                result.history = history
                result.item = items[i]
                result.save()

                print()
                print("result_class:", form.data[f'form-{i}-result_class'])
                print("type(result_class):", type(form.data[f'form-{i}-result_class']))
                print()
                if int(form.data[f'form-{i}-result_class']):
                    labelList.append(chengeLabel(
                            w_size = history.image.image.width,
                            h_size = history.image.image.height,
                            classNum = i + 1,
                            w_min = form.data[f'form-{i}-box_x_min'],
                            h_min = form.data[f'form-{i}-box_y_min'],
                            w_max = form.data[f'form-{i}-box_x_max'],
                            h_max = form.data[f'form-{i}-box_y_max']
                    ))
                    history_coordinate.write('\n')
                    history_coordinate.write(
                        ' '.join(chengeLabel(
                                w_size = history.image.image.width,
                                h_size = history.image.image.height,
                                classNum = i + 1,
                                w_min = form.data[f'form-{i}-box_x_min'],
                                h_min = form.data[f'form-{i}-box_y_min'],
                                w_max = form.data[f'form-{i}-box_x_max'],
                                h_max = form.data[f'form-{i}-box_y_max']
                        ))
                    )
            history_coordinate.close()

            print()
            for i in range(len(labelList)):
                # print(labelList[i])
                print(chengeBox(w_size=history.image.image.width, h_size=history.image.image.height, label=labelList[i]))
            print()

            # file_path = self.object.file_field.path  # ファイルのパス

            asset = Asset.objects.get(id=history.asset.id)
            # Google Drive APIを使用してファイルをアップロード
            for file_path in [history.image.movie.path, history.coordinate.path]: # Google Driveにアップロードされるファイルのパス
            
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    os.path.join(settings.MEDIA_ROOT, settings.SERVICE_ACCOUNT_KEY_NAME), # サービスアカウントキーのJSONファイルへのパス
                    settings.GOOGLE_DRIVE_API_SCOPES, # Google Drive APIのスコープ
                )
                drive_service = build('drive', 'v3', credentials=creds)

                # フォルダを作成
                folder_metadata = {
                    'name': asset.asset_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [settings.GOOGLE_DRIVE_FOLDER_ID],  # アップロード先のGoogle DriveフォルダのID
                }
                folder = drive_service.files().create(body=folder_metadata, fields='id').execute()

                file_metadata = {
                    'name': os.path.basename(file_path),  # アップロードされるファイルの名前
                    'parents': [folder['id']],  # 作成したフォルダのID
                }
                media = MediaFileUpload(file_path, resumable=True)

                uploaded_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            asset.drive_folder_id = folder['id']
            asset.save()

            # print("ttt4", formset)
            messages.success(self.request, 'アイテムを追加しました。')
            return redirect(self.success_url)
            # return super().form_valid(form)

            # return redirect(self.get_redirect_url())
        else:
            ctx["form"] = formset
            print("tttd", form)
            return super().form_invalid(form)
    
    def form_invalid(self, form):
        print("eeef", form)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)


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





class TestPageView(LoginRequiredMixin, generic.CreateView):
    model = Image
    template_name = 'test_page.html'
    pk_url_kwarg = 'id'
    fields = ()
    success_url = reverse_lazy('tracker:asset_list')

    def model_check(self, asset, image):
        
        output_path = os.path.join(settings.MEDIA_ROOT, 'model_check', asset.learning_model.name[8:-3])
        os.makedirs(output_path, exist_ok=True)

        # YOLOモデルの読み込み
        model = YOLO(os.path.join(settings.MEDIA_ROOT, asset.learning_model.name))
        # print("model: ", model, end="\n\n")
        # print("type(model): ", type(model), end="\n\n")

        # 物体検出の実行
        results1 = model.predict(source=os.path.join(settings.MEDIA_ROOT, image.image.name), conf=0.50)
        # results1 = model.predict(
        #     source = os.path.join(settings.MEDIA_ROOT, image.image.name),
        #     save = True,
        #     save_txt = True,
        #     save_conf = True,
        #     conf = 0.50
        # )
        # results2 = model('23.JPG',save=True,save_txt=True,save_conf=True) #当日

        print()
        print("前日")
        
        print()
        print(results1[0])
        # print()
        # print(results1[0].names)
        # print()
        # print(results1[0].boxes)
        # print()
        # print()
        # print(results1[0].boxes.cls.__array__().tolist())
        # print(results1[0].boxes.xyxy.__array__().tolist())
        classDict = results1[0].names
        classNums = results1[0].boxes.cls.__array__().tolist()
        confs = results1[0].boxes.conf.__array__().tolist()
        boxes = results1[0].boxes.xyxy.__array__().tolist()

        # print()
        # print("type", type(results1[0].boxes.cls[0].__array__()))


        print()
        for i in range(len(results1[0].boxes.cls)):
            if round(classNums[i]) and self.box[round(classNums[i])]['conf'] < confs[i]:
                self.box[round(classNums[i])]['box_x_min'] = boxes[i][0]
                self.box[round(classNums[i])]['box_y_min'] = boxes[i][1]
                self.box[round(classNums[i])]['box_x_max'] = boxes[i][2]
                self.box[round(classNums[i])]['box_y_max'] = boxes[i][3]
                self.box[round(classNums[i])]['conf'] = confs[i]

            print(f"{round(classNums[i])}:", classDict[classNums[i]])
            print(f"  x_min = {boxes[i][0]:>20} px")
            print(f"  y_min = {boxes[i][1]:>20} px")
            print(f"  x_max = {boxes[i][2]:>20} px")
            print(f"  y_max = {boxes[i][3]:>20} px")
            # print(f"  y_max = {boxes[i][3]:>20} px")
            print(f"  conf  = {confs[i]:>20} %")
        # print("len", len(results1[0].boxes.cls))
        print()
        # print("当日")
        # print(results2)
        # print("type", type(results2))

        # results1.img.save(os.path.join(output_path, "output_image.jpg"))

        # with open(os.path.join(output_path, "output.txt"), "w") as txt_file:
        #     for i in range(len(results1[0].names)):
        #         txt_file.write(f"{results1[0].names[i]} {results1[0].boxes.xyxy[i]} {results1[0].boxes.conf[i]}\n")

        # with open(os.path.join(output_path, "confidence.txt"), "w") as txt_file:
        #     for conf in results1[0].boxes.conf:
        #         txt_file.write(f"{conf}\n")




    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        asset = Asset.objects.get(id=self.id)
        historys = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').filter(asset=asset).order_by('-updated_at')
        history = historys[0]
        print(historys[0].id)

        # last_history = historys.get(id)
        results = Result.objects.filter(history=historys[0])
        # results = Result.objects.prefetch_related('history').filter(asset=history.asset)
        # result = results.filter(history=history)

        items = Item.objects.filter(asset=history.asset, outer_edge=False)
        result_add_form = forms.formset_factory(
            form = ResultAddForm,
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        
        ttts = re.findall(r'[^0-9]+', self.request.path)
        print("f", ttts)
        # self.id = int(ttt[0])
        # result = Result.objects.filter(history=historys[0])
        # result_class = 0
        # results = Result.objects.filter(history=History.objects.filter(asset=history.asset).order_by('updated_at')[0])
        # if ttts[0] == '/asset-check/':
        # else:
        #     result_class = 1
        #     results = Result.objects.filter(history=historys[0])
        result = Result.objects.prefetch_related('history').filter(history=history).get(result_class=9)
        self.box = [{
            "box_x_min": result.box_x_min,
            "box_y_min": result.box_y_min,
            "box_x_max": result.box_x_max,
            "box_y_max": result.box_y_max,
            "model_check": False,
        }]

        result_class = 0

        result_history = historys.get(id=result.history.id)
        box_x_fix = (result.box_x_max - result.box_x_min) / result_history.image.image.width
        box_y_fix = (result.box_y_max - result.box_y_min) / result_history.image.image.height

        results = Result.objects.filter(history=History.objects.filter(asset=history.asset).order_by('checked_at')[0])#.exclude(result_class=9)
        for i, r in enumerate(results):
            result_history = historys.get(id=r.history.id)
            if not i:
                item_x_fix = (r.box_x_max - r.box_x_min) / result_history.image.image.width
                item_y_fix = (r.box_y_max - r.box_y_min) / result_history.image.image.height
                item_x_min = r.box_x_min
                item_y_min = r.box_y_min
            else:
                item_x_fit = box_x_fix / item_x_fix
                item_y_fit = box_y_fix / item_y_fix
                self.box.append({
                    "box_x_min": ((r.box_x_min - item_x_min) * item_x_fit) + result.box_x_min,
                    "box_y_min": ((r.box_y_min - item_y_min) * item_y_fit) + result.box_y_min,
                    "box_x_max": ((r.box_x_max - item_x_min) * item_x_fit) + result.box_x_min,
                    "box_y_max": ((r.box_y_max - item_y_min) * item_y_fit) + result.box_y_min,
                    # "box_x_min": r.box_x_min,
                    # "box_y_min": r.box_y_min,
                    # "box_x_max": r.box_x_max,
                    # "box_y_max": r.box_y_max,
                    "conf": 0,
                })
        
        if history.asset.learning_model:
            # self.box = []
            # for i in Item.objects.filter(history=history):
            #     self.box
            self.box[0]['model_check'] = True
            print()
            self.model_check(history.asset, history.image)

        extra = {
            "create": result_class,
            "image": history.image.image,
            "items": items.order_by('-id'),
            "results": self.box,
            # "box_x_min": round(result.box_x_min),
            # "box_y_min": round(result.box_y_min),
            # "box_x_max": round(result.box_x_max),
            # "box_y_max": round(result.box_y_max),
            "result_add_form": result_add_form(
                initial = [
                    {
                        'asset': history.asset,
                        'item': x,
                        'image': history.image,
                        'result_class': result_class,
                    } for x in items
                ],
            ),
        }
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context
    

    def form_valid(self, form):
        print("eeeff", self.request.POST)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        history = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').get(id=self.id)
        

        # image = Image.objects.prefetch_related('group').prefetch_related('asset').get(id=self.id)
        
        print("eee", form.data)
        ctx = self.get_context_data()
        items = Item.objects.filter(asset=history.asset, outer_edge=False)
        ttttt = forms.formset_factory(
            form = ResultAddForm,
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        print("fdsf", history.id)
        # history_id = history.objects
        print("fdsf", self.request.FILES)
        formset = ttttt(self.request.POST)
        print("ttt0", formset.forms)
        if formset.is_valid():
            coordinate_path = os.path.join(settings.MEDIA_ROOT, history.coordinate.name)
            history_coordinate = open(coordinate_path, 'a')
            labelList = []
            for i, form in enumerate(formset.forms):

                result = form.save(commit=False)
                # print("eeet", form)
                result.history = history
                result.item = items[i]
                result.save()

                print()
                print("result_class:", form.data[f'form-{i}-result_class'])
                print("type(result_class):", type(form.data[f'form-{i}-result_class']))
                print()
                if int(form.data[f'form-{i}-result_class']):
                    labelList.append(chengeLabel(
                            w_size = history.image.image.width,
                            h_size = history.image.image.height,
                            classNum = i + 1,
                            w_min = form.data[f'form-{i}-box_x_min'],
                            h_min = form.data[f'form-{i}-box_y_min'],
                            w_max = form.data[f'form-{i}-box_x_max'],
                            h_max = form.data[f'form-{i}-box_y_max']
                    ))
                    history_coordinate.write('\n')
                    history_coordinate.write(
                        ' '.join(chengeLabel(
                                w_size = history.image.image.width,
                                h_size = history.image.image.height,
                                classNum = i + 1,
                                w_min = form.data[f'form-{i}-box_x_min'],
                                h_min = form.data[f'form-{i}-box_y_min'],
                                w_max = form.data[f'form-{i}-box_x_max'],
                                h_max = form.data[f'form-{i}-box_y_max']
                        ))
                    )
            history_coordinate.close()

            print()
            for i in range(len(labelList)):
                # print(labelList[i])
                print(chengeBox(w_size=history.image.image.width, h_size=history.image.image.height, label=labelList[i]))
            print()

            # file_path = self.object.file_field.path  # ファイルのパス

            
            # Google Drive APIを使用してファイルをアップロード
            for file_path in [history.image.movie.path, history.coordinate.path]: # Google Driveにアップロードされるファイルのパス
            
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    os.path.join(settings.MEDIA_ROOT, settings.SERVICE_ACCOUNT_KEY_NAME), # サービスアカウントキーのJSONファイルへのパス
                    settings.GOOGLE_DRIVE_API_SCOPES, # Google Drive APIのスコープ
                )
                drive_service = build('drive', 'v3', credentials=creds)

                file_metadata = {
                    'name': os.path.basename(file_path),  # アップロードされるファイルの名前
                    'parents': [settings.GOOGLE_DRIVE_FOLDER_ID],  # アップロード先のGoogle DriveフォルダのID
                }
                media = MediaFileUpload(file_path, resumable=True)

                uploaded_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            # print("ttt4", formset)
            messages.success(self.request, 'アイテムを追加しました。')
            return redirect(self.success_url)
            # return super().form_valid(form)

            # return redirect(self.get_redirect_url())
        else:
            ctx["form"] = formset
            print("tttd", form)
            return super().form_invalid(form)
    
    def form_invalid(self, form):
        print("eeef", form)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)

















class AssetCheckView(LoginRequiredMixin, generic.CreateView):
    # model = Result
    model = Image
    template_name = 'group_join.html'
    pk_url_kwarg = 'id'
    fields = ()
    # form_class = ImageAddForm
    success_url = reverse_lazy('tracker:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)

        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])
        
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

        # print("iii", context['form'])
        assets = Asset.objects.prefetch_related('group').get(id=self.id)
        users = GroupMember.objects.prefetch_related('group').prefetch_related('user')
        image_add_form = ImageAddForm(**self.get_form_kwargs())
        image_add_form.fields['group'].initial = assets.group
        image_add_form.fields['asset'].initial = assets
        image_add_form.fields['user'].initial = users.get(user=self.request.user)
        image_add_form.fields['user'].queryset = users.filter(group=self.id)
        
        items = Item.objects.prefetch_related('group').prefetch_related('asset').filter(asset=self.id)
        result_add_form = forms.formset_factory(
            form = ResultAddForm,
            # form = self.form_class,
            # formset = ResultAddForm(**self.get_form_kwargs()),
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        
        extra = {
            "object": self.object,
            "items": items,
            "image_add_form": image_add_form,
            "result_add_form": result_add_form(
                initial = [
                    {
                        'group': x.group,
                        'asset': x.asset,
                        'item': x,
                        # 'image': images,
                        'result_class': 0,
                    } for x in items
                ],
            ),
        }
        # コンテキスト情報のキーを追加
        context.update(extra)
        return context
    
    def form_valid(self, form):
        print("eeeff", form.data)
        print()
        print("eeeff", self.request.POST['group'])
        print()
        print("eeeff", self.request.FILES['image'])
        print()
        print("eeeff", form.__class__)
        ttt = re.findall(r'\d+', self.request.path)
        self.id = int(ttt[0])


        # image = form.save(commit=False)
        asset = Asset.objects.prefetch_related('group').get(id=self.id)
        image = Image(
            group = asset.group,
            asset = asset,
            user = CustomUser.objects.get(id=self.request.POST['user']),
            image = self.request.FILES['image'],
            taken_at = self.request.POST['taken_at'],
            front = self.request.POST['front']
        )
        image.save()

        history = History(group=image.group, asset=image.asset, user=self.request.user, image=image)
        history.save()
        
        print("eee", form.data)
        ctx = self.get_context_data()
        items = Item.objects.filter(asset=image.asset)
        ttttt = forms.formset_factory(
            form = ResultAddForm,
            extra = items.__len__(),
            max_num = items.__len__(),
        )
        print("ttt", formset.forms)
        
        # for p in self.request.POST:
        #     print("ttt", p)
        print()
        # print("fff", self.fields)
        print("fdsf", ImageAddForm.Meta.fields)
        # print("fdsf", self.request.POST.copy())
        # p = self.request.POST.copy().dict()
        # p = {key: p[key] for key in p.keys() if key not in ['group', 'asset', 'user', 'taken_at', 'initial-taken_at', 'front']} # dict(filter(lambda key: key not in ImageAddForm.Meta.fields, p.keys()))
        # print("ppp", p)
        # print("mmmmm", ImageAddForm.base_fields)
        # print("formset", ttttt())
        post = self.request.POST.copy()
        for key in ['group', 'asset', 'user', 'taken_at', 'initial-taken_at', 'front']:
            post.__delitem__(key)
        print("post", post)
        # print("fdsf", self.request.POST[:-6])
        # history_id = history.objects
        # formset = ttttt(QueryDict(filter(lambda key: key not in ImageAddForm.Meta.fields, self.request.POST.keys())))
        # self.form_class = None
        print()
        print(self.request.POST.get('form-0-box_x_max'))

        # formset = ttttt(self.request.POST)
        formset = ttttt(post)

        # for key in ['group', 'asset', 'user', 'taken_at', 'initial-taken_at', 'front']:
        #     formset().__delitem__(key)

        # formset = ttttt(self.request)
        # print("ttt0f", QueryDict(filter(lambda key: key not in ImageAddForm.Meta.fields, self.request.POST.keys())))
        print()
        print("ttt", formset.get_context()['formset'].data)
        print()
        print("ttt", formset.is_valid())
        print()
        print("ttt0", formset.forms)
        if form.is_valid():
            for formm in formset.forms:
                print()
                print("f", formm.data)
                # for key in ['group', 'asset', 'user', 'taken_at', 'initial-taken_at', 'front']:
                #     formm.__delitem__(key)
                formm.data = post
                print()
                print(formm.data)
                result = formm.save(commit=False)
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
            print()
            print("tttd", form.data)
            messages.error(self.request, "アイテムの追加に失敗しました。")
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