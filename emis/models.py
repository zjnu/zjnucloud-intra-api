import binascii
import datetime
import os

from django.conf import settings
from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class EmisUserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def _create_user(self, username, is_validate, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        user = self.model(username=username, created=now,
                          is_validate=is_validate
                          , is_superuser=is_superuser,
                          **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, username, is_validate=True, **extra_fields):
        return self._create_user(username, is_validate, False, **extra_fields)

    def create_superuser(self, username, is_validate=True, is_superuser=True, **extra_fields):
        return self._create_user(username, is_validate, is_superuser, **extra_fields)


@python_2_unicode_compatible
class BmobUser(models.Model):
    bmob_user = models.CharField(primary_key=True, max_length=255)

    class Meta:
        db_table = 'bmob_user'


@python_2_unicode_compatible
class EmisUser(models.Model):
    username = models.CharField(primary_key=True, max_length=200,)
    # created = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(default=datetime.datetime.now,)
    is_active = models.BooleanField(default=True,)
    is_superuser = models.BooleanField(default=False,)
    bmob_account = models.ForeignKey(BmobUser, null=True, max_length=255,)

    objects = EmisUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'emis_user'

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True


@python_2_unicode_compatible
class Token(models.Model):
    """
    The EMIS authorization token model.
    """
    key = models.CharField(max_length=40, primary_key=True)
    user = models.OneToOneField(EmisUser, related_name='emis_token', to_field='username')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emis_auth_token'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key
