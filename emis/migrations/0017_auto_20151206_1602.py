# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0016_auto_20151206_1548'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='emis_token'),
        ),
    ]
