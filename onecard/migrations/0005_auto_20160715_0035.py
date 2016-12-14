# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onecard', '0004_onecardelectricitybuildings_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='onecardelectricitybuildings',
            name='eventvalidation',
            field=models.TextField(null=True, default=''),
        ),
        migrations.AddField(
            model_name='onecardelectricitybuildings',
            name='viewstate',
            field=models.TextField(null=True, default=''),
        ),
    ]
