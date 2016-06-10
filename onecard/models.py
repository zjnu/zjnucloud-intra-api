import datetime
import binascii
import os

from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from common.models import BmobUser


class OneCardUserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def _create_user(self, username, is_validate, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username.
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
class OneCardUser(models.Model):
    username = models.CharField(primary_key=True, max_length=255,)
    password = models.CharField(default='', max_length=2048,)
    created = models.DateTimeField(default=datetime.datetime.now,)
    is_active = models.BooleanField(default=True,)
    is_superuser = models.BooleanField(default=False,)
    count = models.IntegerField(default=0)
    bmobusers = models.ManyToManyField(BmobUser, db_table='onecard_user_bmobusers')

    objects = OneCardUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'onecard_user'

    def __str__(self):
        return self.username

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True


class OneCardCharge(models.Model):
    code = models.IntegerField(default='')
    message = models.TextField(default='')
    result = models.SmallIntegerField(null=True)
    user = models.ForeignKey(OneCardUser, related_name='charge_user', to_field='username')
    amount = models.TextField(default='', null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'onecard_charge'
        ordering = ('created',)


@python_2_unicode_compatible
class Token(models.Model):
    """
    The EMIS authorization token model.
    """
    key = models.CharField(max_length=40, primary_key=True,)
    user = models.ForeignKey(OneCardUser, related_name='onecard_token', to_field='username',)
    created = models.DateTimeField(auto_now_add=True,)

    class Meta:
        db_table = 'onecard_auth_token'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self):
        # Length of OneCard Token is 21
        return binascii.hexlify(os.urandom(21)).decode()

    def __str__(self):
        return self.key


@receiver(post_save, sender=OneCardUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    Signal to create token after an EMIS user saved
    """
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=OneCardUser)
def remove_auth_token(sender, instance=None, created=False, **kwargs):
    """
    Signal to remove token and itself if no associated BmobUser found
    """
    if not created:
        if instance.count == 0:
            Token.objects.filter(user=instance).delete()
