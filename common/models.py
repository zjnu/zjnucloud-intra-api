from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class BmobUser(models.Model):
    bmob_user = models.CharField(primary_key=True, max_length=255)
    count = models.IntegerField(default=0)

    class Meta:
        db_table = 'emis_bmob_user'

    def __str__(self):
        return self.bmob_user
