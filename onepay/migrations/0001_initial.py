# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import onepay.models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnePayUser',
            fields=[
                ('username', models.CharField(serialize=False, max_length=255, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('count', models.IntegerField(default=0)),
                ('bmobusers', models.ManyToManyField(to='common.BmobUser', db_table='onepay_user_bmobusers')),
            ],
            options={
                'db_table': 'onepay_user',
            },
            managers=[
                ('objects', onepay.models.OnePayUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(serialize=False, max_length=40, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='onepay_token', to='onepay.OnePayUser')),
            ],
            options={
                'db_table': 'onepay_auth_token',
            },
        ),
    ]
