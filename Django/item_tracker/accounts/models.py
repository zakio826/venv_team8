from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """拡張ユーザーモデル"""
    
    class Meta:
        verbose_name_plural = 'CustomUser'

class Group(models.Model):
    """グループモデル"""
    
    user = models.ForeignKey(CustomUser, verbose_name='ホストユーザ', on_delete=models.PROTECT)
    group_name = models.CharField(verbose_name='グループ名', max_length=40)
    
    class Meta: verbose_name_plural = 'Group'
    
    def __str__(self):
        return self.group_name