# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0004_auto_20151127_1925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='username',
            field=models.CharField(max_length=200),
        ),
    ]
