# Generated by Django 4.2.5 on 2023-09-19 05:55

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
                ('checked_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='確認日時')),
                ('updated_at', models.DateTimeField(verbose_name='更新日時')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.asset', verbose_name='管理項目')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.group', verbose_name='グループ')),
            ],
            options={
                'verbose_name_plural': 'History',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='', verbose_name='写真')),
                ('taken_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='撮影日時')),
                ('front', models.BooleanField(default=False, verbose_name='サムネイル')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.asset', verbose_name='管理項目')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.group', verbose_name='グループ')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='撮影ユーザー')),
            ],
            options={
                'verbose_name_plural': 'Image',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=40, verbose_name='アイテム名')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.asset', verbose_name='管理項目')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.group', verbose_name='グループ')),
            ],
            options={
                'verbose_name_plural': 'Item',
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_class', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(7)], verbose_name='詳細結果')),
                ('box_x_min', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (x_min)')),
                ('box_y_min', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (y_min)')),
                ('box_x_max', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (x_max)')),
                ('box_y_max', models.FloatField(blank=True, null=True, verbose_name='バウンディングボックス (y_max)')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.asset', verbose_name='管理項目')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.group', verbose_name='グループ')),
                ('history', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.history', verbose_name='履歴')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.image', verbose_name='写真')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.item', verbose_name='アイテム')),
            ],
            options={
                'verbose_name_plural': 'Result',
            },
        ),
        migrations.AddField(
            model_name='history',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.image', verbose_name='写真'),
        ),
        migrations.AddField(
            model_name='history',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='確認ユーザー'),
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.group', verbose_name='グループ')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='メンバー')),
            ],
            options={
                'verbose_name_plural': 'GroupMember',
            },
        ),
        migrations.AddField(
            model_name='asset',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.group', verbose_name='グループ'),
        ),
    ]
