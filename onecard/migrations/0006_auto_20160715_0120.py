# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onecard', '0005_auto_20160715_0035'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OneCardElectricityBuildings',
            new_name='OneCardElectricityRoom',
        ),
        migrations.AlterModelTable(
            name='onecardelectricityroom',
            table='dict_onecard_electricity_rooms',
        ),
    ]
