# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0008_auto_20151129_2212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='bmob_account',
            field=models.ForeignKey(max_length=255, to='emis.BmobUser', null=True),
        ),
    ]
