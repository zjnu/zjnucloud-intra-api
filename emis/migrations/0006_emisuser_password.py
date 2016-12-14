# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0005_auto_20160628_1349'),
    ]

    operations = [
        migrations.AddField(
            model_name='emisuser',
            name='password',
            field=models.CharField(max_length=191, default=''),
        ),
    ]
