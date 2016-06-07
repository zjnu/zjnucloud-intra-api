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
                ('bmob_user', models.CharField(primary_key=True, serialize=False, max_length=255)),
                ('count', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'emis_bmob_user',
            },
        ),
    ]
