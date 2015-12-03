# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0006_auto_20151128_1949'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emisuser',
            name='bind_time',
        ),
    ]
