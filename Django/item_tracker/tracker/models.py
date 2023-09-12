from accounts.models import CustomUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from datetime import datetime

class Group(models.Model):
    """グループモデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='ホストユーザ', on_delete=models.PROTECT)
    group_name = models.CharField(verbose_name='グループ名', max_length=40)
    
    class Meta:
        verbose_name_plural = 'Group'
    
    def __str__(self):
        return self.group_name

class GroupMember(models.Model):
    """グループモデル"""
    
    member = models.ForeignKey(CustomUser, verbose_name='メンバー', on_delete=models.PROTECT)
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)
    
    class Meta:
        verbose_name_plural = 'GroupMember'
    
    def __str__(self):
        return self.member

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
    
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    item_name = models.CharField(verbose_name='アイテム名', max_length=40)
    
    class Meta:
        verbose_name_plural = 'Item'
    
    def __str__(self):
        return self.item_name

class Image(models.Model):
    """画像モデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='撮影ユーザ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    image = models.ImageField(verbose_name='写真')
    taken_at = models.DateTimeField(verbose_name='撮影日時', default=datetime.now)
    
    class Meta:
        verbose_name_plural = 'Image'
    
    def __str__(self):
        return self.asset

class History(models.Model):
    """履歴モデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='確認ユーザ', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    image = models.ForeignKey(Image, verbose_name='写真', on_delete=models.PROTECT)
    checked_at = models.DateTimeField(verbose_name='確認日時', default=datetime.now)
    updated_at = models.DateTimeField(verbose_name='更新日時')

    def save(self, *args, **kwargs):
        auto_now = kwargs.pop('updated_at_auto_now', True)
        if auto_now:
            self.updated_at = datetime.now()
        super(History, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Image'
    
    def __str__(self):
        return self.asset

class Result(models.Model):
    """アイテム別履歴モデル"""
    
    history = models.ForeignKey(History, verbose_name='履歴', on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, verbose_name='管理項目', on_delete=models.PROTECT)
    image = models.ForeignKey(Image, verbose_name='写真', on_delete=models.PROTECT)
    item = models.ForeignKey(Item, verbose_name='アイテム', on_delete=models.PROTECT)
    result_class = models.IntegerField(verbose_name='詳細結果', validators=[MinValueValidator(0), MaxValueValidator(7)])
    box_x_min = models.FloatField(verbose_name='バウンディングボックス (x_min)')
    box_y_min = models.FloatField(verbose_name='バウンディングボックス (y_min)')
    box_x_max = models.FloatField(verbose_name='バウンディングボックス (x_max)')
    box_y_max = models.FloatField(verbose_name='バウンディングボックス (y_max)')

    class Meta:
        verbose_name_plural = 'Result'
    
    def __str__(self):
        return self.item