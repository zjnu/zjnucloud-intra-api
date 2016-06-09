# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import onecard.models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneCardUser',
            fields=[
                ('username', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('password', models.CharField(default='', max_length=2048)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('count', models.IntegerField(default=0)),
                ('bmobusers', models.ManyToManyField(db_table='onecard_user_bmobusers', to='common.BmobUser')),
            ],
            options={
                'db_table': 'onecard_user',
            },
            managers=[
                ('objects', onecard.models.OneCardUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='onecard_token', to='onecard.OneCardUser')),
            ],
            options={
                'db_table': 'onecard_auth_token',
            },
        ),
    ]
