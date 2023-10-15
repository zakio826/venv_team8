from accounts.models import CustomUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

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
    
    user = models.ForeignKey(CustomUser, verbose_name='メンバー', on_delete=models.PROTECT)
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    
    class Meta:
        verbose_name_plural = 'GroupMember'
    
    def __str__(self):
        return self.group.group_name + "_" + self.user.username

class Asset(models.Model):
    """管理項目モデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset_name = models.CharField(verbose_name='管理名', max_length=40)

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
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)

    item_name = models.CharField(verbose_name='アイテム名', max_length=40)
    outer_edge = models.BooleanField(verbose_name='外枠', default=False)
    
    class Meta:
        verbose_name_plural = 'Item'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.item_name

class Image(models.Model):
    """画像モデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    user = models.ForeignKey(CustomUser, verbose_name='撮影ユーザー', on_delete=models.PROTECT)

    movie = models.FileField(
        upload_to='movie/',
        verbose_name='動画',
        # validators=[FileExtensionValidator(['pdf', ])],
    )
    image = models.ImageField(upload_to='image/', verbose_name='写真', blank=True, null=True)
    taken_at = models.DateTimeField(verbose_name='撮影日時', default=datetime.now)
    front = models.BooleanField(verbose_name='サムネイル', default=False)

    def save(self, *args, **kwargs):
        
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'movie'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'image'), exist_ok=True)
        
        # 親クラスのsaveメソッドを呼び出す
        super().save(*args, **kwargs)

        # # アップロードされた動画ファイルのパスを取得
        # video_path = os.path.join(settings.MEDIA_ROOT, str(self.movie))
        # print()
        # print("self.movie:", self.movie)
        # # print("video_path:", video_path)
        # print()
        
        # #動画のプロパティを取得
        # cap = cv2.VideoCapture(video_path)
        # width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # fps = cap.get(cv2.CAP_PROP_FPS)

        # total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # # mp4に変換するコード
        # output_path = os.path.splitext(video_path)[0] + '.mp4'
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用するコーデックを指定

        # # cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        # # cap
        
        # out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))  # 出力ファイルの設定
        
        # print("cap_frame_b:", cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # # print("out_frame:", out.get(cv2.CAP_PROP_FRAME_COUNT))
        # print()
        

        # tm = cv2.TickMeter() # fps測定用
        # tme = cv2.TickMeter() #Set_time測定用
        # tm.start()
        # tme.start()
        # count = 0
        # max_count = 10
        # fps = 0
        # elasp_time = 0
        # set_time = 5

        # cnt = 0

        # for i in range(total_frame):
        #     ret, frame = cap.read()
        #     # Resize the window
        #     # windowsize = (800, 600)
        #     # frame = cv2.resize(frame, windowsize)
        #     # print(ret)

        #     if ret is True:

        #         # Display the resulting frame
        #         # cv2.imshow('frame', frame)

        #         # Write the frame
        #         out.write(frame)
        #         tme.stop()
        #         elasp_time = tme.getTimeSec()
        #         tme.start()

        #         if count == max_count:
        #             tm.stop()
        #             time_el = tm.getTimeSec()
        #             fps = max_count / time_el
        #             elasp_time = elasp_time + time_el
        #             tm.reset()
        #             tm.start()
        #             count = 0

        #         print('FPS: {:>6.2f}, 1/FPS[ms]: {:>9.2f}, movie[s]:{:>6.2f} '.format(fps,(1/(fps+0.01))*1000,elasp_time))
        #         #1/(fps+0.01)は0で割る止まってしまうため便宜上fps+0.01としている。

        #         count += 1

        #         # if cv2.waitKey(1) & 0xFF == ord('q'):
        #         #     print('break')
        #         #     break

        #         if elasp_time > set_time:
        #             print('Break by Time out')
        #             ret = False
        #             break
        #     else:
        #         cnt += 1
        #         now_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        #         if now_frame < total_frame and elasp_time < set_time:
        #             cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        #             continue
        #         break

        # # Release everything if job is finished
        # tm.stop()
        # tm.reset()
        # tme.stop()
        # tme.reset()
        # cap.release()
        # out.release()

        # print("cnt:", cnt)
        # # print("frame_num:", cnt)
        # # print("out_frame:", out.get(cv2.CAP_PROP_FRAME_COUNT))
        # # print()
        # # print("frame:", frame)
        # # print()
        
        # # cap.release()
        # # out.release()

        # cv2.destroyAllWindows()
    
        # # 変換後のファイルを保存
        # self.movie.name = os.path.relpath(output_path, settings.MEDIA_ROOT)

        # 先頭の1フレームを取得してImageFieldに保存
        # cap = cv2.VideoCapture(output_path)
        cap = cv2.VideoCapture(os.path.join(settings.MEDIA_ROOT, str(self.movie)))
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
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    user = models.ForeignKey(CustomUser, verbose_name='確認ユーザー', on_delete=models.PROTECT)
    image = models.ForeignKey(Image, verbose_name='写真', on_delete=models.PROTECT)
    
    coordinate = models.FileField(upload_to='coordinate/', verbose_name='座標ファイル', blank=True, null=True,
        # validators=[FileExtensionValidator(['pdf', ])],
    )

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
    
    history = models.ForeignKey(History, verbose_name='履歴', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    item = models.ForeignKey(Item, verbose_name='アイテム', on_delete=models.PROTECT)
    image = models.ForeignKey(Image, verbose_name='写真', on_delete=models.PROTECT)

    result_class = models.IntegerField(verbose_name='詳細結果', validators=[MinValueValidator(0), MaxValueValidator(7)])
    # result_class = {0: '無し', 1: '手動確認', 9: '外枠'}
    box_x_min = models.FloatField(verbose_name='バウンディングボックス (x_min)', blank=True, null=True)
    box_y_min = models.FloatField(verbose_name='バウンディングボックス (y_min)', blank=True, null=True)
    box_x_max = models.FloatField(verbose_name='バウンディングボックス (x_max)', blank=True, null=True)
    box_y_max = models.FloatField(verbose_name='バウンディングボックス (y_max)', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Result'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.item.item_name + "_" + self.history.updated_at.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')