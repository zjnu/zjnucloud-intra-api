# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onecard', '0003_onecardelectricitybuildings'),
    ]

    operations = [
        migrations.AddField(
            model_name='onecardelectricitybuildings',
            name='value',
            field=models.CharField(default='', max_length=32),
        ),
    ]
