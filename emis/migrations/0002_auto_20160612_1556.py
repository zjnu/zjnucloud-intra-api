# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
