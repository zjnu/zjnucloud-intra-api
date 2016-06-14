# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BmobUser',
            fields=[
                ('id', models.IntegerField(serialize=False, auto_created=True, primary_key=True, default=0)),
                ('bmob_user', models.CharField(max_length=191)),
                ('count', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'emis_bmob_user',
            },
        ),
    ]
