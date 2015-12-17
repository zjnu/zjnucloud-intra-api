# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('emis', '0015_remove_emisuser_is_authenticated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emisuser',
            name='bmob_account',
            field=models.OneToOneField(primary_key=True, to='emis.BmobUser', max_length=255, serialize=False),
        ),
        migrations.AlterField(
            model_name='emisuser',
            name='username',
            field=models.CharField(unique=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='token',
            name='user',
            field=models.OneToOneField(to_field='username', related_name='emis_token', to=settings.AUTH_USER_MODEL),
        ),
    ]
