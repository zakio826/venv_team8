from django.contrib.auth.models import AbstractUser
from tracker.models import Group
from django.db import models

class CustomUser(AbstractUser):
    """拡張ユーザーモデル"""
    
    group = models.ForeignKey(Group, verbose_name='グループ', on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = 'CustomUser'

