# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0018_auto_20151206_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='bmob_account',
            field=models.ForeignKey(to='emis.BmobUser', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='emisuser',
            name='username',
            field=models.CharField(primary_key=True, serialize=False, max_length=200),
        ),
    ]
