# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onecard', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onecardcharge',
            name='id',
            field=models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True),
        ),
        migrations.AlterField(
            model_name='onecarduser',
            name='id',
            field=models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True),
        ),
    ]
