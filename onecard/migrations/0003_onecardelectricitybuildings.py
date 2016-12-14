# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onecard', '0002_auto_20160617_1634'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneCardElectricityBuildings',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('building', models.CharField(default='', max_length=191)),
                ('room', models.CharField(default='', max_length=191)),
            ],
            options={
                'db_table': 'dict_onecard_electricity_buildings',
            },
        ),
    ]
