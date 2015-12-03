# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0013_auto_20151202_1900'),
    ]

    operations = [
        migrations.AddField(
            model_name='emisuser',
            name='is_authenticated',
            field=models.BooleanField(default=True),
        ),
    ]
