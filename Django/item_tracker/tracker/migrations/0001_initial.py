# Generated by Django 4.2.5 on 2023-10-24 03:26

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_name', models.CharField(max_length=40, verbose_name='管理名')),
                ('drive_folder_id', models.CharField(blank=True, null=True, verbose_name='フォルダID')),
                ('learning_model', models.FileField(blank=True, null=True, upload_to='learning/', verbose_name='学習モデル')),
            ],
            options={
                'verbose_name_plural': 'Asset',
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_name', models.CharField(max_length=40, null=True, verbose_name='グループ名')),
                ('private', models.BooleanField(default=True, verbose_name='個人利用')),
                ('group_id', models.CharField(max_length=12, unique=True, verbose_name='グループID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='ホストユーザー')),
            ],
            options={
                'verbose_name_plural': 'Group',
            },
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coordinate', models.FileField(blank=True, null=True, upload_to='coordinate/', verbose_name='座標ファイル')),
                ('checked_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='確認日時')),
                ('updated_at', models.DateTimeField(blank=True, null=True, verbose_name='更新日時')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.asset', verbose_name='管理項目')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='tracker.group', verbose_name='グループ')),
            ],
            options={
                'verbose_name_plural': 'History',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=40, verbose_name='アイテム名')),
                ('outer_edge', models.BooleanField(default=False, verbose_name='外枠')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.asset', verbose_name='管理項目')),
            ],
            options={
                'verbose_name_plural': 'Item',
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_class', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(9)], verbose_name='詳細結果')),
                ('box_x_min', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (x_min)')),
                ('box_y_min', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (y_min)')),
                ('box_x_max', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (x_max)')),
                ('box_y_max', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (y_max)')),
                ('history', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.history', verbose_name='履歴')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.item', verbose_name='アイテム')),
            ],
            options={
                'verbose_name_plural': 'Result',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movie', models.FileField(upload_to='movie/', validators=[django.core.validators.FileExtensionValidator(['mp4'])], verbose_name='動画')),
                ('image', models.ImageField(blank=True, null=True, upload_to='image/', verbose_name='写真')),
                ('taken_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='撮影日時')),
                ('front', models.BooleanField(default=False, verbose_name='サムネイル')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.asset', verbose_name='管理項目')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='tracker.group', verbose_name='グループ')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='撮影ユーザー')),
            ],
            options={
                'verbose_name_plural': 'Image',
            },
        ),
        migrations.AddField(
            model_name='history',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.image', verbose_name='写真'),
        ),
        migrations.AddField(
            model_name='history',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='確認ユーザー'),
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.group', verbose_name='グループ')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='メンバー')),
            ],
            options={
                'verbose_name_plural': 'GroupMember',
            },
        ),
        migrations.AddField(
            model_name='asset',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.group', verbose_name='グループ'),
        ),
    ]
