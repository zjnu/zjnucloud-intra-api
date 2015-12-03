# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0010_auto_20151130_1138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emisuser',
            name='user_id',
        ),
        migrations.AlterField(
            model_name='emisuser',
            name='username',
            field=models.CharField(max_length=200, primary_key=True, serialize=False),
        ),
    ]
