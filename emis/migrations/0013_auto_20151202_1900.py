# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0012_auto_20151130_2048'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emisuser',
            old_name='is_validate',
            new_name='is_active',
        ),
        migrations.AlterField(
            model_name='emisuser',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
