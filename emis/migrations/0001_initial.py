# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmisUser',
            fields=[
                ('user_id', models.IntegerField(serialize=False, primary_key=True)),
                ('username', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_validate', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'emis_user',
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(serialize=False, primary_key=True, max_length=40)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(to='emis.EmisUser')),
            ],
            options={
                'db_table': 'emis_auth_token',
            },
        ),
    ]
