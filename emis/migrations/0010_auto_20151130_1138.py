# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0009_auto_20151130_0906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='user_id',
            field=models.IntegerField(auto_created=True, primary_key=True, serialize=False),
        ),
    ]
