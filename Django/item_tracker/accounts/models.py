from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """拡張ユーザーモデル
    superuser: team8 (pass: team8888)
    user: zakio (pass: fukui8888)
    """

    class Meta:
        verbose_name_plural = 'CustomUser'

