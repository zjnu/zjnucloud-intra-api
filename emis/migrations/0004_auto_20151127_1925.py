# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0003_auto_20151125_2316'),
    ]

    operations = [
        migrations.AddField(
            model_name='emisuser',
            name='bind_time',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='emisuser',
            name='bmob_account',
            field=models.CharField(max_length=255, default=1),
            preserve_default=False,
        ),
    ]
