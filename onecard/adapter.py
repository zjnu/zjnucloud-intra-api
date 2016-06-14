from django.core.exceptions import ObjectDoesNotExist
from common.models import BmobUser
from onecard.models import OneCardUser


class OneCardAccountAdapter:

    def get_onecard_user(self, username):
        """
        Get or instantiates a new EMIS user instance.
        """
        user, created = OneCardUser.objects.get_or_create(username=username)
        return user

    def get_bmob_user(self, username):
        """
        Get or instantiates a new Bmob user instance.
        """
        user, created = BmobUser.objects.get_or_create(bmob_user=username)
        return user

    def save_onecard_user(self, user, data, commit=True):
        """
        Saves a new `OneCardUser` instance using information provided in the
        request data.
        """
        setattr(user, 'username', data.get('username'))
        setattr(user, 'password', data.get('password'))
        setattr(user, 'count', user.count + 1)
        if commit:
            user.save()
        return user

    def save_bmob_user(self, user, data, commit=True):
        """
        Saves the BmobUser related to OneCardUser
        """
        bmob_username = data.get('bmob')
        setattr(user, 'bmob_user', bmob_username)
        setattr(user, 'count', user.count)
        if commit:
            user.save()
        return user

    def delete_onecard_user(self, data):
        """
        Find OneCardUser and its BmobUser, delete the relation
        :param data: request.data
        :return: Boolean
        """
        try:
            onecard_username = data['username']
            bmob_username = data['bmob']
            bmob_user = BmobUser.objects.get(bmob_user=bmob_username)
            onecard_user = OneCardUser.objects.get(username=onecard_username)
            # Count > 1, minus 1, else delete()
            onecard_user.count -= 1
            bmob_user.onecarduser_set.remove(onecard_user)

            # TODO: Deal with bmob_user.count when add BmobUser limit
            # if bmob_user.count > 1:
            #     bmob_user.count -= 1
            #     onecard_user.count -= 1
            #     bmob_user.emisuser_set.remove(onecard_user)
            #     bmob_user.save()
            # else:
            #     onecard_user.count -= 1
            #     bmob_user.delete()

            onecard_user.save()
            return True
        except KeyError:
            return False
        except ObjectDoesNotExist:
            return False

    def get_association(self, data):
        """
        Get correlate BmobUser and OneCardUser objects
        :param data: request.data
        :return: A tuple (Boolean, BmobUser, OneCardUser)
        """
        try:
            onecard_user = OneCardUser.objects.get(username=data['username'])
            bmob_user = onecard_user.bmobusers.get(bmob_user=data['bmob'])
            return True, onecard_user, bmob_user
        except ObjectDoesNotExist:
            return False, None, None


def get_adapter():
    return OneCardAccountAdapter()
