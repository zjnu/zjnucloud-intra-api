from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from . import app_settings
from emis.models import BmobUser


class EmisAccountAdapter(object):

    def stash_verified_email(self, request, email):
        request.session['account_verified_email'] = email

    def unstash_verified_email(self, request):
        ret = request.session.get('account_verified_email')
        request.session['account_verified_email'] = None
        return ret

    def is_email_verified(self, request, email):
        """
        Checks whether or not the email address is already verified
        beyond allauth scope, for example, by having accepted an
        invitation before signing up.
        """
        ret = False
        verified_email = request.session.get('account_verified_email')
        if verified_email:
            ret = verified_email.lower() == email.lower()
        return ret

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse
        """
        return True

    def new_user(self, request):
        """
        Instantiates a new User instance.
        """
        user = get_user_model()()
        return user

    def new_bmob_user(self, request):
        """
        Instantiates a new Bmob user instance.
        """
        user = BmobUser()
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

    def save_user(self, request, user, bmob_user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        from .utils import user_username, user_bmobuser

        data = form.cleaned_data
        username = data.get('username')
        user_username(user, username)
        user_bmobuser(user, bmob_user)
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

        data = form.cleaned_data
        username = data.get('bmob')
        setattr(user, 'bmob_user', username)
        if commit:
            user.save()
        return user

    def clean_username(self, username):
        """
        Validates the username. You can hook into this if you want to
        (dynamically) restrict what usernames can be chosen.
        """

        # TODO: Add regexp support to USERNAME_BLACKLIST
        username_blacklist_lower = [ub.lower()
                                    for ub in app_settings.USERNAME_BLACKLIST]
        if username.lower() in username_blacklist_lower:
            raise ValidationError(_("Username can not be used. "
                                          "Please use other username."))
        username_field = 'username'
        assert username_field
        user_model = get_user_model()
        try:
            query = {username_field + '__iexact': username}
            user_model.objects.get(**query)
        except user_model.DoesNotExist:
            return username
        raise ValidationError(_("This username is already taken. Please "
                                      "choose another."))

    def clean_password(self, password):
        """
        Validates a password. You can hook into this if you want to
        restric the allowed password choices.
        """
        min_length = app_settings.PASSWORD_MIN_LENGTH
        if len(password) < min_length:
            raise ValidationError(_("Password must be a minimum of {0} "
                                          "characters.").format(min_length))
        return password

    def login(self, request, user):
        from django.contrib.auth import login
        # HACK: This is not nice. The proper Django way is to use an
        # authentication backend
        if not hasattr(user, 'backend'):
            user.backend \
                = "allauth.account.auth_backends.AuthenticationBackend"
        login(request, user)

    def confirm_email(self, request, email_address):
        """
        Marks the email address as confirmed on the db
        """
        email_address.verified = True
        email_address.set_as_primary(conditional=True)
        email_address.save()

    def set_password(self, user, password):
        user.set_password(password)
        user.save()

    def is_safe_url(self, url):
        from django.utils.http import is_safe_url
        return is_safe_url(url)


def get_adapter():
    return EmisAccountAdapter()
