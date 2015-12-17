# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0017_auto_20151206_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='username',
            field=models.CharField(max_length=200),
        ),
    ]
