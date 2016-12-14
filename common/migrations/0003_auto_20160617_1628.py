# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_auto_20160612_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bmobuser',
            name='id',
            field=models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID'),
        ),
    ]
