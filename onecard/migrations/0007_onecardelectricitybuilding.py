# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onecard', '0006_auto_20160715_0120'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneCardElectricityBuilding',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=32, default='')),
                ('viewstate', models.TextField(default='', null=True)),
                ('eventvalidation', models.TextField(default='', null=True)),
            ],
            options={
                'db_table': 'dict_onecard_electricity_buildings',
            },
        ),
    ]
