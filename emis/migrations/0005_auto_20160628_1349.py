# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0004_auto_20160628_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='scores_last_update',
            field=models.DateTimeField(null=True, default=None),
        ),
    ]
