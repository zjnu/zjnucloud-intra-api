# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0005_auto_20151128_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='BmobUser',
            fields=[
                ('bmob_user', models.CharField(primary_key=True, serialize=False, max_length=255)),
            ],
            options={
                'db_table': 'bmob_user',
            },
        ),
        migrations.AlterField(
            model_name='emisuser',
            name='bmob_account',
            field=models.ForeignKey(to='emis.BmobUser'),
        ),
    ]
