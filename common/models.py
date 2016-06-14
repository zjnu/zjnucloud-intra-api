from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class BmobUser(models.Model):
    id = models.IntegerField(default=0, primary_key=True, auto_created=True)
    bmob_user = models.CharField(max_length=191)
    count = models.IntegerField(default=0)

    class Meta:
        db_table = 'bmob_user'

    def __str__(self):
        return self.bmob_user


# @python_2_unicode_compatible
# class Relation(models.Model):
#     id = models.IntegerField(default=0, primary_key=True, auto_created=True)
#     emisuser_id = models.CharField(max_length=200)
#     bmobuser_id = models.CharField(max_length=255)
#
#     class Meta:
#         db_table = 'emis_user_bmobusers'
