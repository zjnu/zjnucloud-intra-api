from django.core.exceptions import ObjectDoesNotExist
from common.models import BmobUser
from onepay.models import OnePayUser


class OnePayAccountAdapter:

    def get_onepay_user(self, username):
        """
        Get or instantiates a new EMIS user instance.
        """
        user, created = OnePayUser.objects.get_or_create(username=username)
        return user

    def get_bmob_user(self, username):
        """
        Get or instantiates a new Bmob user instance.
        """
        user, created = BmobUser.objects.get_or_create(bmob_user=username)
        return user

    def save_onepay_user(self, user, data, commit=True):
        """
        Saves a new `OnePayUser` instance using information provided in the
        request data.
        """
        username = data.get('username')
        setattr(user, 'username', username)
        setattr(user, 'count', user.count + 1)
        if commit:
            user.save()
        return user

    def save_bmob_user(self, user, data, commit=True):
        """
        Saves the BmobUser related to OnePayUser
        """
        bmob_username = data.get('bmob')
        setattr(user, 'bmob_user', bmob_username)
        setattr(user, 'count', user.count)
        if commit:
            user.save()
        return user

    def get_association(self, data):
        """
        Get correlate BmobUser and OnePayUser objects
        :param data: request.data
        :return: A tuple (Boolean, BmobUser, OnePayUser)
        """
        try:
            onepay_user = OnePayUser.objects.get(username=data['username'])
            bmob_user = onepay_user.bmobusers.get(pk=data['bmob'])
            return True, onepay_user, bmob_user
        except ObjectDoesNotExist:
            return False, None, None


def get_adapter():
    return OnePayAccountAdapter()
