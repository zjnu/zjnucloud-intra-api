from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from . import app_settings
from emis.models import BmobUser


class EmisAccountAdapter(object):

    def get_emis_user(self, form):
        """
        Get or instantiates a new EMIS user instance.
        """
        username = form.cleaned_data.get('username')
        user, created = get_user_model().objects.get_or_create(username=username)
        return user

    def get_bmob_user(self, form):
        """
        Get or instantiates a new Bmob user instance.
        """
        username = form.cleaned_data.get('bmob')
        user, created = BmobUser.objects.get_or_create(bmob_user=username)
        return user

    def populate_username(self, request, user):
        """
        Fills in a valid username, if required and missing.  If the
        username is already present it is assumed to be valid
        (unique).
        """
        from .utils import user_username
        username = user_username(user)
        if app_settings.USER_MODEL_USERNAME_FIELD:
            user_username(user, username)

    def save_emis_user(self, request, user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        from .utils import user_username, user_count

        data = form.cleaned_data
        username = data.get('username')
        user_username(user, username)
        # Atomic counter
        user_count(user, user.count + 1)
        self.populate_username(request, user)
        if commit:
            # Ability not to commit makes it easier to derive from
            # this adapter by adding
            user.save()
        return user

    def save_bmob_user(self, request, user, form, commit=True):
        """
        Saves the Bmob user related to EMIS user
        """
        from .utils import user_count

        data = form.cleaned_data
        bmob_username = data.get('bmob')
        setattr(user, 'bmob_user', bmob_username)
        # Atomic counter
        user_count(user, user.count + 1)
        if commit:
            user.save()
        return user

    def login(self, request, user):
        from django.contrib.auth import login
        # HACK: This is not nice. The proper Django way is to use an
        # authentication backend
        if not hasattr(user, 'backend'):
            user.backend \
                = "allauth.account.auth_backends.AuthenticationBackend"
        login(request, user)

    def set_password(self, user, password):
        user.set_password(password)
        user.save()

    def is_association_exists(self, form):
        """
        :return: A tuple(Boolean, EmisUser). If association exists, return True and its
                 EmisUser object, otherwise return (False, None)
        """
        try:
            emis_username = form.cleaned_data.get('username')
            emis_user = get_user_model().objects.get(username=emis_username)
            bmob_username = form.cleaned_data.get('bmob')
            bmob_user = emis_user.bmobusers.get(bmob_user=bmob_username)
            return True, emis_user, bmob_user
        except ObjectDoesNotExist:
            return False, None, None

    def is_safe_url(self, url):
        from django.utils.http import is_safe_url
        return is_safe_url(url)


def get_adapter():
    return EmisAccountAdapter()
