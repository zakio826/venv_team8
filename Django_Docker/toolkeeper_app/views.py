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

from django.core.paginator import Paginator
from django.http import Http404

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
from googleapiclient.http import MediaIoBaseDownload
import shutil

from ultralytics import YOLO


class IndexView(generic.TemplateView):
    template_name = "index.html"


class InquiryView(generic.FormView):
    template_name = "inquiry.html"
    form_class = InquiryForm
    success_url = reverse_lazy('toolkeeper_app:inquiry')

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'メッセージを送信しました。')
        logger.info('Inquiry sent by {}'.format(form.cleaned_data['name']))
        return super().form_valid(form)

class AssetListView(LoginRequiredMixin, generic.ListView):
    model = Asset
    template_name = 'asset_list.html'
    context_object_name = 'image_list'

    def get_queryset(self):
        group = self.request.GET.get('group')  # フォームから選択されたグループ

        belong = GroupMember.objects.prefetch_related('group').filter(user=self.request.user)
        images = Image.objects.prefetch_related('group').prefetch_related('asset').filter(front=True)
        
        if group and group != 'all':  # 特定のグループが選択された場合
            images = images.filter(group=group)
        elif len(belong) >= 1:
            user_groups = [group.group for group in belong]
            images = images.filter(group__in=user_groups)

        return images

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context['image_list'], 3)
        page = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page)

        # フォームをユーザー情報とともにインスタンス化
        context['group_filter_form'] = GroupFilterForm(user=self.request.user, data=self.request.GET)

        return context

class AssetDetailView(LoginRequiredMixin, generic.DetailView):
    model = Asset
    template_name = 'asset_detail.html'
    pk_url_kwarg = 'id'

    # ファイルをダウンロードするメソッド
    def download_file(self, file_id, file_name):
        # Google Driveからファイルをダウンロードするためのリクエストを作成
        request = self.drive_service.files().get_media(fileId=file_id)
        # ローカルにファイルを保存するためのファイルハンドラを開き、ファイルをバイナリ書き込みモードで開いている
        fh = open(os.path.join(settings.MEDIA_ROOT, 'learning', file_name), 'wb')
        # メディアファイルをダウンロードするためのダウンローダーを作成
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        # ダウンロードが完了するまでループし、進捗を表示している
        while done is False:
            status, done = downloader.next_chunk()
            print(f'Download {file_name} {int(status.progress() * 100)}%')

        # ダウンロードが完了したら、ファイルパスをデータベースに保存している
        self.asset.learning_model.name = os.path.join('learning', self.pt_file_name)
        self.asset.save()

    # フォルダ内のファイルを再帰的にダウンロードするメソッド
    def download_folder(self, folder_id, target_folder_name):
        # フォルダ内のファイルを検索するためのクエリを設定
        query = f"'{folder_id}' in parents"
        # クエリを実行し、ファイルリストを取得
        results = self.drive_service.files().list(q=query).execute()
        files = results.get('files', [])

        # フォルダ内の各ファイルに対して処理を実行
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                # もしファイルがフォルダであれば、再帰的にフォルダを作成し中身をダウンロード
                subfolder_id = file['id']
                subfolder_name = file['name']
                subfolder_path = os.path.join(os.path.join(os.path.join(settings.MEDIA_ROOT, 'learning'), target_folder_name), subfolder_name)
                os.makedirs(subfolder_path, exist_ok=True)
                self.download_folder(subfolder_id, target_folder_name)
            else:
                # ファイルであればダウンロード
                file_id = file['id']
                file_name = file['name']
                if file_name == self.pt_file_name:
                    self.download_file(file_id, file_name)

    # ファイルの拡張子が'.pt'であるフォルダの名前を取得するメソッド
    def get_pt_folder_name(self):
        query = f"'{self.asset.drive_folder_id}' in parents"
        results = self.drive_service.files().list(q=query).execute()
        files = results.get('files', [])

        for file in files:
            file_name = file['name']
            ext = os.path.splitext(file_name)[1]
            if ext == '.pt':
                return os.path.splitext(file_name)[0]

    # コンテキストデータを取得するメソッド
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Assetモデルのインスタンスを取得し、関連するデータを取得
        self.asset = get_object_or_404(Asset, id=self.object.id)
        self.historys = History.objects.prefetch_related('image').filter(asset=self.asset).order_by('-updated_at')
        self.pt_file_name = os.path.splitext(self.historys[0].image.movie.name[6:])[0] + '.pt'
        
        # Google Driveからファイルをダウンロードするためのセットアップ
        if self.asset.drive_folder_id:
            service_account_key_path = settings.SERVICE_ACCOUNT_KEY_ROOT
            creds = service_account.Credentials.from_service_account_file(
                service_account_key_path,
                scopes=settings.GOOGLE_DRIVE_API_SCOPES,
            )
            self.drive_service = build('drive', 'v3', credentials=creds)

            # '.pt'フォルダの名前を取得し、フォルダ内のファイルをダウンロード
            pt_folder_name = self.get_pt_folder_name()

            if pt_folder_name:
                self.download_folder(self.asset.drive_folder_id, pt_folder_name)
            else:
                print("ptファイルが見つかりません。またはエラーが発生しました。")

        # コンテキストに追加のデータを設定
        extra = {
            "object": self.object,
            "image_list": Image.objects.prefetch_related('asset').filter(asset=self.object.id).filter(front=True),
            "item_list": Item.objects.prefetch_related('asset').filter(asset=self.object.id, outer_edge=False),
            "asset_id": self.object.id,
            "historys": History.objects.prefetch_related('asset').prefetch_related('user').filter(asset_id=self.object.id),
        }
        context.update(extra)
        return context
    
class AssetCreateView(LoginRequiredMixin, generic.CreateView):
    model = Asset
    template_name = 'asset_create.html'
    form_class = AssetCreateForm
    success_url = reverse_lazy('toolkeeper_app:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # コンテキストデータを取得
        context = super().get_context_data(**kwargs)
        
        # ユーザーが所属するグループを取得
        belongs = GroupMember.objects.prefetch_related('group').filter(user=self.request.user)
        group_list = []

        for b in belongs:
            group_list.append(Group.objects.filter(id=b.group.id))

        groups = group_list[0]

        # 複数のグループを結合
        if len(group_list) >= 2:
            for g in group_list[1:]:
                groups = groups | g

        # フォームのgroupフィールドのクエリセットを設定
        context['form'].fields['group'].queryset = groups

        # 追加のコンテキスト情報を設定
        extra = {
            "object": self.object,
        }

        # コンテキスト情報を更新
        context.update(extra)
        return context

    # フォームが有効な場合の処理
    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.save()

        # 成功時のリダイレクトURLを設定
        self.success_url = reverse_lazy(f'toolkeeper_app:image_add', kwargs={'id': asset.id})
        messages.success(self.request, '管理項目を作成しました。')
        return super().form_valid(form)
    
    # フォームが無効な場合の処理
    def form_invalid(self, form):
        messages.error(self.request, "管理項目の作成に失敗しました.")
        return super().form_invalid(form)
    

class ImageAddView(LoginRequiredMixin, generic.CreateView):
    model = Image
    template_name = 'image_add.html'
    pk_url_kwarg = 'id'
    fields = ()
    item_add_form = ItemAddForm
    image_add_form = ImageAddForm
    history_add_form = HistoryAddForm
    result_add_form = ResultAddForm
    success_url = reverse_lazy('toolkeeper_app:asset_list')

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)

        # コンテキストに追加するフォームを初期化
        image_add_form = self.image_add_form(**self.get_form_kwargs())
        history_add_form = self.history_add_form(**self.get_form_kwargs())
        result_add_form = self.result_add_form(**self.get_form_kwargs())
        item_add_form = None

        # アセット情報を取得
        asset = Asset.objects.prefetch_related('group').get(id=self.kwargs[self.pk_url_kwarg])

        # フォームにユーザー情報を初期化
        image_add_form['user'].initial = self.request.user

        # ヒストリフォームにユーザー情報を初期化し、非表示に設定
        history_add_form['user'].initial = self.request.user
        history_add_form['user'].field.widget = forms.HiddenInput()

        # リザルトフォームの初期化
        result_add_form['result_class'].initial = 9
        result_add_form['result_class'].field.widget = forms.HiddenInput()

        # URLから情報を抽出
        url_parts = re.findall(r'[^0-9]+', self.request.path)
        if url_parts[0] == '/asset-create/image-add/':
            image_add_form['user'].field.widget = forms.HiddenInput()
            item_add_form = self.item_add_form(**self.get_form_kwargs())
            item_add_form['item_name'].initial = "外枠"
            item_add_form['item_name'].field.widget = forms.HiddenInput()
            submit = "登録"
        else:
            members = GroupMember.objects.prefetch_related('group').prefetch_related('user')
            user_list = []

            for m in members.filter(group=asset.group):
                user_list.append(CustomUser.objects.filter(id=m.user.id))

            users = user_list[0]

            if len(user_list) >= 2:
                for u in user_list[1:]:
                    users = users | u

            image_add_form['user'].field.queryset = users
            submit = "追加"

        # 追加したいコンテキスト情報を設定
        extra = {
            "submit": submit,
            "object": self.object,
            "image_add_form": image_add_form,
            "item_add_form": item_add_form,
            "result_add_form": result_add_form,
        }

        # コンテキスト情報を更新
        context.update(extra)
        return context

    # フォームが有効な場合の処理
    def form_valid(self, form):
        ttts = re.findall(r'[^0-9]+', self.request.path)

        asset = Asset.objects.prefetch_related('group').get(id=self.kwargs[self.pk_url_kwarg])

        image_form = self.image_add_form(self.request.POST, self.request.FILES)
        image_form = image_form.save(commit=False)
        image_form.group = asset.group
        image_form.asset = asset
        image_form.user = self.request.user
        if ttts[0] == '/asset-create/image-add/':
            image_form.front = True
        image_form.save()
        image = Image.objects.get(id=image_form.id)

        if ttts[0] == '/asset-create/image-add/':
            item_form = self.item_add_form(self.request.POST)
            item_form = item_form.save(commit=False)
            item_form.asset = asset
            item_form.outer_edge = True
            item_form.save()
        item = Item.objects.filter(outer_edge=True).get(asset=asset)

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
                w_size=image.image.width,
                h_size=image.image.height,
                classNum=0,
                w_min=form.data['box_x_min'],
                h_min=form.data['box_y_min'],
                w_max=form.data['box_x_max'],
                h_max=form.data['box_y_max']
            ))
        )
        history_coordinate.close()

        result = self.result_add_form(self.request.POST).save(commit=False)
        result.history = history
        result.item = item
        result.result_class = 9
        result.save()

        self.id = history.id

        if ttts[0] == '/asset-create/image-add/':
            self.success_url = reverse_lazy(f'toolkeeper_app:item_add', kwargs={'id': self.id})
            messages.success(self.request, '写真を登録しました。')
        else:
            self.success_url = reverse_lazy(f'toolkeeper_app:asset_check', kwargs={'id': self.id})
            messages.success(self.request, '写真を追加しました.')

        return redirect(self.success_url)

    # フォームが無効な場合の処理
    def form_invalid(self, form):
        messages.error(self.request, "写真の登録に失敗しました。")
        return super().form_invalid(form)


class ItemAddView(LoginRequiredMixin, generic.CreateView):
    model = Item
    template_name = 'item_add.html'
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('toolkeeper_app:asset_list')
    formset = forms.formset_factory(form=ItemAddForm)
    fields = ()

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)

        # URLから情報を抽出
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
        print(settings.MEDIA_ROOT)

        # コンテキスト情報を更新
        context.update(extra)
        return context

    # フォームが有効な場合の処理
    def form_valid(self, form):
        history = History.objects.prefetch_related('group').prefetch_related('asset').get(id=self.kwargs[self.pk_url_kwarg])

        # フォームセットを初期化
        formset = self.formset(self.request.POST)

        if formset.is_valid():
            for forms in formset:
                item = forms.save(commit=False)
                item.asset = history.asset
                item.save()

            self.success_url = reverse_lazy(f'toolkeeper_app:history_add', kwargs={'id': self.kwargs[self.pk_url_kwarg]})
            messages.success(self.request, 'アイテムを追加しました。')
            return redirect(self.success_url)

        else:
            return self.form_invalid(form)
    
    # フォームが無効な場合の処理
    def form_invalid(self, form):
        messages.error(self.request, "アイテムの追加に失敗しました。")
        return super().form_invalid(form)


class HistoryAddView(LoginRequiredMixin, generic.CreateView):
    model = Image
    template_name = 'history_add.html'
    pk_url_kwarg = 'id'
    fields = ()
    success_url = reverse_lazy('toolkeeper_app:asset_list')

    # 物体検出を行うヘルパーメソッド
    def model_check(self, asset, image):
        # YOLOモデルを読み込み
        output_path = os.path.join(settings.MEDIA_ROOT, 'model_check', asset.learning_model.name[8:-3])
        os.makedirs(output_path, exist_ok=True)
        model = YOLO(os.path.join(settings.MEDIA_ROOT, asset.learning_model.name))

        # 物体検出を実行し、結果を解析
        results1 = model.predict(source=os.path.join(settings.MEDIA_ROOT, image.image.name))
        classNums = results1[0].boxes.cls.__array__().tolist()
        confs = results1[0].boxes.conf.__array__().tolist()
        boxes = results1[0].boxes.xyxy.__array__().tolist()

        for i in range(len(results1[0].boxes.cls)):
            if round(classNums[i]) and self.box[round(classNums[i])]['conf'] < confs[i]:
                self.box[round(classNums[i])]['box_x_min'] = boxes[i][0]
                self.box[round(classNums[i])]['box_y_min'] = boxes[i][1]
                self.box[round(classNums[i])]['box_x_max'] = boxes[i][2]
                self.box[round(classNums[i])]['box_y_max'] = boxes[i][3]
                self.box[round(classNums[i])]['conf'] = confs[i]

    # get_context_dataをオーバーライド
    def get_context_data(self, **kwargs):
        # 既存のget_context_dataをコール
        context = super().get_context_data(**kwargs)
        historys = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').order_by('-updated_at')
        history = historys.get(id=self.kwargs[self.pk_url_kwarg])

        # ヒストリの結果を取得
        results = Result.objects.filter(history=historys[0])
        items = Item.objects.filter(asset=history.asset, outer_edge=False)

        # 結果追加フォームのフォームセットを生成
        result_add_form = forms.formset_factory(
            form=ResultAddForm,
            extra=items.__len__(),
            max_num=items.__len__(),
        )

        ttts = re.findall(r'[^0-9]+', self.request.path)

        # ボックス情報を初期化
        result = Result.objects.prefetch_related('history').filter(history=history).get(result_class=9)
        self.box = [{
            "box_x_min": result.box_x_min,
            "box_y_min": result.box_y_min,
            "box_x_max": result.box_x_max,
            "box_y_max": result.box_y_max,
            "model_check": False,
        }]

        # 判定モードを設定
        if ttts[0] == '/asset-check/':
            result_class = 0

            result_history = historys.get(id=result.history.id)
            box_x_fix = (result.box_x_max - result.box_x_min) / result_history.image.image.width
            box_y_fix = (result.box_y_max - result.box_y_min) / result_history.image.image.height

            results = Result.objects.filter(history=History.objects.filter(asset=history.asset).order_by('checked_at')[0])

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
                self.box[0]['model_check'] = True
                self.model_check(history.asset, history.image)
        else:
            result_class = 1

        extra = {
            "create": result_class,
            "image": history.image.image,
            "items": items.order_by('-id'),
            "results": self.box,
            "threshold_conf": 0.79,
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
        context.update(extra)
        return context
    
    # フォームが有効な場合の処理
    def form_valid(self, form):
        history = History.objects.prefetch_related('group').prefetch_related('asset').prefetch_related('image').get(id=self.kwargs[self.pk_url_kwarg])

        ctx = self.get_context_data()
        items = Item.objects.filter(asset=history.asset, outer_edge=False)
        ttttt = forms.formset_factory(
            form=ResultAddForm,
            extra=items.__len__(),
            max_num=items.__len__(),
        )

        formset = ttttt(self.request.POST)

        if formset.is_valid():
            coordinate_path = os.path.join(settings.MEDIA_ROOT, history.coordinate.name)
            history_coordinate = open(coordinate_path, 'a')
            labelList = []

            for i, form in enumerate(formset.forms):
                result = form.save(commit=False)
                result.history = history
                result.item = items[i]
                result.save()

                if int(form.data[f'form-{i}-result_class']):
                    labelList.append(chengeLabel(
                            w_size=history.image.image.width,
                            h_size=history.image.image.height,
                            classNum=i + 1,
                            w_min=form.data[f'form-{i}-box_x_min'],
                            h_min=form.data[f'form-{i}-box_y_min'],
                            w_max=form.data[f'form-{i}-box_x_max'],
                            h_max=form.data[f'form-{i}-box_y_max']
                    ))
                    history_coordinate.write('\n')
                    history_coordinate.write(
                        ' '.join(chengeLabel(
                                w_size=history.image.image.width,
                                h_size=history.image.image.height,
                                classNum=i + 1,
                                w_min=form.data[f'form-{i}-box_x_min'],
                                h_min=form.data[f'form-{i}-box_y_min'],
                                w_max=form.data[f'form-{i}-box_x_max'],
                                h_max=form.data[f'form-{i}-box_y_max']
                        ))
                    )
            history_coordinate.close()

            for i in range(len(labelList)):
                print(chengeBox(w_size=history.image.image.width, h_size=history.image.image.height, label=labelList[i]))

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                # os.path.join(settings.MEDIA_ROOT, settings.SERVICE_ACCOUNT_KEY_NAME),
                settings.SERVICE_ACCOUNT_KEY_ROOT,
                settings.GOOGLE_DRIVE_API_SCOPES
            )
            drive_service = build('drive', 'v3', credentials=creds)

            asset = Asset.objects.get(id=history.asset.id)

            if not asset.drive_folder_id:
                folder_metadata = {
                    'name': str(asset.asset_name),
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [settings.GOOGLE_DRIVE_FOLDER_ID],
                }

                folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
                asset.drive_folder_id = folder['id']
                asset.save()

            for file_path in [history.image.movie.path, history.coordinate.path]:
                file_metadata = {
                    'name': os.path.basename(file_path),
                    'parents': [str(asset.drive_folder_id)],
                }
                media = MediaFileUpload(file_path, resumable=True)

                uploaded_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            messages.success(self.request, '履歴を追加しました.')
            return redirect(self.success_url)
        else:
            ctx["form"] = formset
            messages.error(self.request, "履歴の追加に失敗しました.")
            return super().form_invalid(form)

    # フォームが無効な場合の処理
    def form_invalid(self, form):
        messages.error(self.request, "履歴の追加に失敗しました.")
        return super().form_invalid(form)


class HistoryListView(LoginRequiredMixin, generic.ListView):
    model = History
    template_name = 'history_list.html'
    context_object_name = 'history_list'
    paginate_by = 9

    def get_queryset(self):
        user_groups = GroupMember.objects.filter(user=self.request.user).values_list('group', flat=True)
        history_list = History.objects.filter(group__in=user_groups)

        selected_group = self.request.GET.get('group')
        if selected_group:
            history_list = history_list.filter(group=selected_group)

        # ソート条件を取得
        sort_order = self.request.GET.get('sort_order')
        if sort_order == 'asc':
            history_list = history_list.order_by('updated_at')
        elif sort_order == 'desc':
            history_list = history_list.order_by('-updated_at')

        return history_list

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_groups = GroupMember.objects.filter(user=self.request.user).values_list('group', flat=True)
        context['sort_form'] = SortForm(data=self.request.GET)

        history_list = History.objects.filter(group__in=user_groups)
        page = self.request.GET.get('page')

        # フォームをユーザー情報とともにインスタンス化
        context['group_filter_form'] = GroupFilterForm(user=self.request.user, data=self.request.GET)

        return context
    
    

class HistoryDetailView(LoginRequiredMixin, generic.DetailView):
    model = History
    template_name = 'history_detail.html'
    context_object_name = 'history'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        return context

















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



@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']
            
            # グループIDの自動生成と重複チェック
            group_id = generate_unique_group_id()
            
            group = form.save(commit=False)
            group.user = request.user
            group.group_id = group_id
            group.save()

            GroupMember.objects.create(user=request.user, group=group)

            return redirect('toolkeeper_app:index')

    else:
        form = GroupForm()

    return render(request, 'create_group.html', {'form': form})

import secrets
import string

def generate_unique_group_id():
    while True:
        group_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        if not Group.objects.filter(group_id=group_id).exists():
            return group_id


@login_required
def join_group(request):
    if request.method == 'POST':
        form = JoinGroupForm(request.POST)
        if form.is_valid():
            group_id = form.cleaned_data['group_id']

            try:
                group = Group.objects.get(group_id=group_id)
            except Group.DoesNotExist:
                messages.error(request, '提供されたグループIDが存在しません。正しいグループIDを入力してください.')
            else:
                if group.private:
                    messages.error(request, 'このグループは個人利用グループであり、参加できません.')
                else:
                    user_already_in_group = GroupMember.objects.filter(user=request.user, group=group).exists()
                    if user_already_in_group:
                        messages.error(request, '既にこのグループに参加しています.')
                    else:
                        GroupMember.objects.create(user=request.user, group=group)
                        return redirect('toolkeeper_app:group_list')

    else:
        form = JoinGroupForm()

    return render(request, 'join_group.html', {'form': form})


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    members_count = group.groupmember_set.count()

    if request.method == 'POST' and 'delete_group' in request.POST:
        # 削除確認のための URL にリダイレクト
        return redirect('toolkeeper_app:group_delete', group_id=group_id)

    return render(request, 'group_detail.html', {'group': group, 'members_count': members_count})

@login_required
def group_delete(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    if request.method == 'POST' and 'confirm_delete' in request.POST:
        group.delete()
        messages.success(request, 'グループが削除されました。')
        return redirect('toolkeeper_app:group_list')
    elif request.method == 'POST' and 'cancel_delete' in request.POST:
        return redirect('toolkeeper_app:group_detail', group_id=group_id)

    return render(request, 'group_delete.html', {'group': group})

@login_required
def group_list(request):
    user_groups = GroupMember.objects.filter(user=request.user)
    return render(request, 'group_list.html', {'user_groups': user_groups})





class TestPageView(LoginRequiredMixin, generic.CreateView):
    model = Image
    template_name = 'test_page.html'
    pk_url_kwarg = 'id'
    fields = ()
    success_url = reverse_lazy('toolkeeper_app:asset_list')

    def model_check(self, asset, image):
        
        # YOLOモデルの読み込み
        model = YOLO(os.path.join(settings.MEDIA_ROOT, asset.learning_model.name))
        # print("model: ", model, end="\n\n")
        # print("type(model): ", type(model), end="\n\n")

        # 物体検出の実行
        # results1 = model.predict(source=os.path.join(settings.MEDIA_ROOT, image.image.name), conf=0.50)
        results1 = model.predict(
            source = os.path.join(settings.MEDIA_ROOT, image.image.name),
            save = True,
            save_txt = True,
            save_conf = True,
            # conf = 0.50,
        )
        # results2 = model('23.JPG',save=True,save_txt=True,save_conf=True) #当日
        
        print()
        # print(results1[0])
        # print()

        # 保存されたファイルを移動する
        # output_path = os.path.join(settings.MEDIA_ROOT, 'model_check')
        model_name = os.path.splitext(asset.learning_model.name[9:])[0]
        image_name = os.path.splitext(image.image.name[6:])[0]
        output_path = os.path.join(settings.MEDIA_ROOT, 'model_check', model_name)

        # print("tt0", model_name)
        # print()
        # print("tt1", output_path)
        # print()
        # print("tt2", os.path.join(str(results1[0].save_dir), f'{image_name}.jpg'))
        # print()
        # print("tt3", os.path.join(str(results1[0].save_dir), 'labels', f'{image_name}.txt'))
        # print()
        # print("tt4", os.path.join(output_path, f'{image_name}.jpg'))
        # print()
        # print("tt5", os.path.join(output_path, f'{image_name}.txt'))

        os.makedirs(output_path, exist_ok=True)

        runs_path = os.path.split(str(results1[0].save_dir))[0][:-7]

        shutil.move(os.path.join(str(results1[0].save_dir), f'{image_name}.jpg'), os.path.join(output_path, f'{image_name}.jpg'))
        shutil.move(os.path.join(str(results1[0].save_dir), 'labels', f'{image_name}.txt'), os.path.join(output_path, f'{image_name}.txt'))
        shutil.rmtree(runs_path)

        # print()
        # print("前日")
        
        # print(results1[0])
        # print()
        # print("tt", str(results1[0].save_dir)[:-15])
        # print("tt", results1[0].save_dir)
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

            print(f"{classDict[classNums[i]]:>2}. {self.items[round(classNums[i])].item_name} (conf: {confs[i] * 100:>5.02f} %)")
            print(f"   x_min = {boxes[i][0] :>20.15f} px")
            print(f"   y_min = {boxes[i][1] :>20.15f} px")
            print(f"   x_max = {boxes[i][2] :>20.15f} px")
            print(f"   y_max = {boxes[i][3] :>20.15f} px")
            # print(f"conf  = {confs[i]*100:>20.15f} %")
            print()

        print("len", len(results1[0].boxes.cls))
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
            self.items = Item.objects.filter(asset=history.asset)

            self.box[0]['model_check'] = True
            print()
            self.model_check(history.asset, history.image)

        # print("self.box:")
        # print(self.box)

        extra = {
            "create": result_class,
            "image": history.image.image,
            "items": items.order_by('-id'),
            "results": self.box,
            "threshold_conf": 0.69,
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
                    # os.path.join(settings.MEDIA_ROOT, settings.SERVICE_ACCOUNT_KEY_NAME), # サービスアカウントキーのJSONファイルへのパス
                    settings.SERVICE_ACCOUNT_KEY_ROOT, # サービスアカウントキーのJSONファイルへのパス
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
