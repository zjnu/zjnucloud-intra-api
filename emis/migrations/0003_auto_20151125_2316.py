# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import emis.models


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0002_auto_20151124_1344'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='emisuser',
            managers=[
                ('objects', emis.models.EmisUserManager()),
            ],
        ),
        migrations.AddField(
            model_name='emisuser',
            name='is_superuser',
            field=models.BooleanField(default=False),
        ),
    ]
