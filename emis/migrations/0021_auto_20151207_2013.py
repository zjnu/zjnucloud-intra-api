# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0020_auto_20151206_1724'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emisuser',
            name='bmob_account',
        ),
        migrations.AddField(
            model_name='bmobuser',
            name='count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='emisuser',
            name='bmobusers',
            field=models.ManyToManyField(to='emis.BmobUser', db_table='emis_user_bmobusers'),
        ),
        migrations.AddField(
            model_name='emisuser',
            name='count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='emisuser',
            name='username',
            field=models.CharField(primary_key=True, max_length=255, serialize=False),
        ),
        migrations.AlterModelTable(
            name='bmobuser',
            table='emis_bmob_user',
        ),
    ]
