from accounts.models import CustomUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from datetime import datetime

class Group(models.Model):
    """グループモデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='ホストユーザー', on_delete=models.PROTECT)
    group_name = models.CharField(verbose_name='グループ名', max_length=40, blank=False, null=True)
    private = models.BooleanField(verbose_name='個人利用', default=True)
    
    class Meta:
        verbose_name_plural = 'Group'
    
    def __str__(self):
        return self.group_name

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
    
    class Meta:
        verbose_name_plural = 'Asset'
    
    def __str__(self):
        return self.asset_name

class Item(models.Model):
    """アイテムモデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)

    item_name = models.CharField(verbose_name='アイテム名', max_length=40)
    
    class Meta:
        verbose_name_plural = 'Item'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.item_name

class Image(models.Model):
    """画像モデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    user = models.ForeignKey(CustomUser, verbose_name='撮影ユーザー', on_delete=models.PROTECT)

    image = models.ImageField(verbose_name='写真')
    taken_at = models.DateTimeField(verbose_name='撮影日時', default=datetime.now)
    front = models.BooleanField(verbose_name='サムネイル', default=False)
    
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

    checked_at = models.DateTimeField(verbose_name='確認日時', default=datetime.now)
    updated_at = models.DateTimeField(verbose_name='更新日時')

    def save(self, *args, **kwargs):
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
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    item = models.ForeignKey(Item, verbose_name='アイテム', on_delete=models.PROTECT)
    image = models.ForeignKey(Image, verbose_name='写真', on_delete=models.PROTECT)

    result_class = models.IntegerField(verbose_name='詳細結果', validators=[MinValueValidator(0), MaxValueValidator(7)])
    box_x_min = models.FloatField(verbose_name='バウンディングボックス (x_min)', blank=True, null=True)
    box_y_min = models.FloatField(verbose_name='バウンディングボックス (y_min)', blank=True, null=True)
    box_x_max = models.FloatField(verbose_name='バウンディングボックス (x_max)', blank=True, null=True)
    box_y_max = models.FloatField(verbose_name='バウンディングボックス (y_max)', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Result'
    
    def __str__(self):
        return self.asset.asset_name + "_" + self.item.item_name + "_" + self.history.updated_at.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')