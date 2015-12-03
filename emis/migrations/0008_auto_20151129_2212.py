# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0007_remove_emisuser_bind_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='bmob_account',
            field=models.ForeignKey(null=True, to='emis.BmobUser'),
        ),
    ]
