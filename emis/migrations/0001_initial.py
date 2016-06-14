# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import emis.models
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmisUser',
            fields=[
                ('id', models.IntegerField(auto_created=True, serialize=False, default=0, primary_key=True)),
                ('username', models.CharField(max_length=191)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('count', models.IntegerField(default=0)),
                ('bmobusers', models.ManyToManyField(db_table='emis_user_bmobusers', to='common.BmobUser')),
            ],
            options={
                'db_table': 'emis_user',
            },
            managers=[
                ('objects', emis.models.EmisUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(serialize=False, primary_key=True, max_length=40)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='emis_token', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'emis_auth_token',
            },
        ),
    ]
