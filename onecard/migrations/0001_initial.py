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
            name='OneCardCharge',
            fields=[
                ('id', models.IntegerField(auto_created=True, primary_key=True, default=0, serialize=False)),
                ('code', models.IntegerField()),
                ('message', models.TextField(default='')),
                ('result', models.SmallIntegerField(null=True)),
                ('amount', models.TextField(null=True, default='')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('created',),
                'db_table': 'onecard_charge',
            },
        ),
        migrations.CreateModel(
            name='OneCardUser',
            fields=[
                ('id', models.IntegerField(auto_created=True, primary_key=True, default=0, serialize=False)),
                ('username', models.CharField(max_length=191)),
                ('password', models.CharField(max_length=2048, default='')),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('count', models.IntegerField(default=0)),
                ('bmobusers', models.ManyToManyField(to='common.BmobUser', db_table='onecard_user_bmobusers')),
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
                ('key', models.CharField(max_length=191, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('user', models.ForeignKey(related_name='onecard_token', to='onecard.OneCardUser')),
            ],
            options={
                'db_table': 'onecard_auth_token',
            },
        ),
        migrations.AddField(
            model_name='onecardcharge',
            name='user',
            field=models.ForeignKey(related_name='charge_user', to='onecard.OneCardUser'),
        ),
    ]
