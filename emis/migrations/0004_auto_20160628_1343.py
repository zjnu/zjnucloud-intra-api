# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0003_auto_20160617_1628'),
    ]

    operations = [
        migrations.AddField(
            model_name='emisuser',
            name='scores',
            field=models.TextField(null=True, default=''),
        ),
        migrations.AddField(
            model_name='emisuser',
            name='scores_last_update',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
