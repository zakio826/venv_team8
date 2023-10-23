from accounts.models import CustomUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, FileExtensionValidator

from django.conf import settings

from datetime import datetime
from PIL import Image
from io import BytesIO
import os
import cv2
import re
import shutil

class Group(models.Model):
    """グループモデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='ホストユーザー', on_delete=models.PROTECT)
    group_name = models.CharField(verbose_name='グループ名', max_length=40, blank=False, null=True)
    private = models.BooleanField(verbose_name='個人利用', default=True)
    
    class Meta:
        verbose_name_plural = 'Group'
    
    def __str__(self):
        return self.group_name + "_" + self.user.username

class GroupMember(models.Model):
    """グループメンバーモデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='メンバー', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = 'GroupMember'
    
    def __str__(self):
        return self.group.group_name + "_" + self.user.username

class Asset(models.Model):
    """管理項目モデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.CASCADE)
    asset_name = models.CharField(verbose_name='管理名', max_length=40)

    drive_folder_id = models.CharField(verbose_name='フォルダID', blank=True, null=True)
    learning_model = models.FileField(
        upload_to='learning/',
        verbose_name='学習モデル',
        blank=True,
        null=True,
    )
    
    class Meta:
        verbose_name_plural = 'Asset'
    
    def __str__(self):
        return self.group.group_name + "_" + self.asset_name
    
    def save(self, *args, **kwargs):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'learning'), exist_ok=True)
        
        # 親クラスのsaveメソッドを呼び出す
        super().save(*args, **kwargs)

class Item(models.Model):
    """アイテムモデル"""
    
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.CASCADE)

    item_name = models.CharField(verbose_name='アイテム名', max_length=40)
    outer_edge = models.BooleanField(verbose_name='外枠', default=False)
    
    def save(self, *args, **kwargs):

        # 親クラスのsaveメソッドを呼び出す
        super().save(*args, **kwargs)

        if self.outer_edge:
            self.item_name = "外枠"

        # 最終的に保存
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = 'Item'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.item_name

class Image(models.Model):
    """画像モデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.DO_NOTHING)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, verbose_name='撮影ユーザー', null=True, on_delete=models.SET_NULL)

    movie = models.FileField(
        upload_to='movie/',
        verbose_name='動画',
        validators=[FileExtensionValidator(['mp4', ])],
    )
    image = models.ImageField(upload_to='image/', verbose_name='写真', blank=True, null=True)

    taken_at = models.DateTimeField(verbose_name='撮影日時', default=datetime.now)
    front = models.BooleanField(verbose_name='サムネイル', default=False)

    def save(self, *args, **kwargs):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'movie'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'image'), exist_ok=True)
        
        # 親クラスのsaveメソッドを呼び出す
        super().save(*args, **kwargs)

        # 先頭の1フレームを取得してImageFieldに保存
        output_path = os.path.join(settings.MEDIA_ROOT, str(self.movie))
        cap = cv2.VideoCapture(output_path)

        print("cap_frame_a:", cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print()

        ret, frame = cap.read()
        if ret:
            output_path = os.path.join(settings.MEDIA_ROOT, 'image', self.movie.name[6:])
            image_path = os.path.splitext(output_path)[0] + '.jpg'
            cv2.imwrite(image_path, frame)

            self.image.name = os.path.relpath(image_path, settings.MEDIA_ROOT)
        
        # 最終的に保存
        super().save(*args, **kwargs)

    
    class Meta:
        verbose_name_plural = 'Image'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.taken_at.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')

class History(models.Model):
    """履歴モデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.DO_NOTHING)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, verbose_name='確認ユーザー', null=True, on_delete=models.SET_NULL)
    image = models.ForeignKey(Image, verbose_name='写真', on_delete=models.CASCADE)
    
    coordinate = models.FileField(upload_to='coordinate/', verbose_name='座標ファイル', blank=True, null=True,)

    checked_at = models.DateTimeField(verbose_name='確認日時', default=datetime.now)
    updated_at = models.DateTimeField(verbose_name='更新日時', blank=True, null=True)

    def save(self, *args, **kwargs):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'coordinate'), exist_ok=True)

        output_path = os.path.join(settings.MEDIA_ROOT, 'coordinate', self.image.image.name[6:])
        coordinate_path = os.path.splitext(output_path)[0] + '.txt'

        coordinate = open(coordinate_path, 'w')
        coordinate.close()

        self.coordinate.name = os.path.relpath(coordinate_path, settings.MEDIA_ROOT)

        auto_now = kwargs.pop('updated_at_auto_now', True)
        if auto_now:
            self.updated_at = datetime.now()
        super(History, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'History'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.updated_at.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')

class Result(models.Model):
    """アイテム別履歴モデル"""
    
    history = models.ForeignKey(History, verbose_name='履歴', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, verbose_name='アイテム', on_delete=models.CASCADE)

    result_class = models.IntegerField(verbose_name='詳細結果', validators=[MinValueValidator(0), MaxValueValidator(9)])
    # result_class = {0: '無し', 1: '手動確認', 2: '学習済みモデル確認', 9: '外枠'}
    box_x_min = models.FloatField(verbose_name='バウンディングボックス (x_min)', blank=True, null=True)
    box_y_min = models.FloatField(verbose_name='バウンディングボックス (y_min)', blank=True, null=True)
    box_x_max = models.FloatField(verbose_name='バウンディングボックス (x_max)', blank=True, null=True)
    box_y_max = models.FloatField(verbose_name='バウンディングボックス (y_max)', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Result'
    
    def __str__(self):
        return self.history.asset.asset_name + "_" + self.item.item_name + "_" + self.history.updated_at.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')