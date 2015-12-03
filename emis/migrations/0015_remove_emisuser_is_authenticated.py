# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0014_emisuser_is_authenticated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emisuser',
            name='is_authenticated',
        ),
    ]
