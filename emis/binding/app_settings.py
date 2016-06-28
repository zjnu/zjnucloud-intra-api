class AppSettings(object):

    class AuthenticationMethod:
        USERNAME = 'username'
        EMAIL = 'email'
        USERNAME_EMAIL = 'username_email'

    class EmailVerificationMethod:
        # After signing up, keep the user account inactive until the email
        # address is verified
        MANDATORY = 'mandatory'
        # Allow login with unverified e-mail (e-mail verification is
        # still sent)
        OPTIONAL = 'optional'
        # Don't send e-mail verification mails during signup
        NONE = 'none'

    def __init__(self, prefix):
        self.prefix = prefix

    def _setting(self, name, dflt):
        from django.conf import settings
        getter = getattr(settings,
                         'ALLAUTH_SETTING_GETTER',
                         lambda name, dflt: getattr(settings, name, dflt))
        return getter(self.prefix + name, dflt)

    @property
    def BMOB_USER_LIMIT(self):
        return 5

    @property
    def EMIS_USER_LIMIT(self):
        return 10

    @property
    def SPECIAL_USER(self):
        return ['zjnucloud-from-public']

    @property
    def DEFAULT_HTTP_PROTOCOL(self):
        return self._setting("DEFAULT_HTTP_PROTOCOL", "http")

    @property
    def AUTHENTICATION_METHOD(self):
        from django.conf import settings
        if hasattr(settings, "ACCOUNT_EMAIL_AUTHENTICATION"):
            import warnings
            warnings.warn("ACCOUNT_EMAIL_AUTHENTICATION is deprecated,"
                          " use ACCOUNT_AUTHENTICATION_METHOD",
                          DeprecationWarning)
            if getattr(settings, "ACCOUNT_EMAIL_AUTHENTICATION"):
                ret = self.AuthenticationMethod.EMAIL
            else:
                ret = self.AuthenticationMethod.USERNAME
        else:
            ret = self._setting("AUTHENTICATION_METHOD",
                                self.AuthenticationMethod.USERNAME)
        return ret

    @property
    def SIGNUP_PASSWORD_VERIFICATION(self):
        """
        Signup password verification
        """
        return self._setting("SIGNUP_PASSWORD_VERIFICATION", True)

    @property
    def PASSWORD_MIN_LENGTH(self):
        """
        Minimum password Length
        """
        return self._setting("PASSWORD_MIN_LENGTH", 6)

    @property
    def SIGNUP_FORM_CLASS(self):
        """
        Signup form
        """
        return self._setting("SIGNUP_FORM_CLASS", None)

    @property
    def USERNAME_REQUIRED(self):
        """
        The user is required to enter a username when signing up
        """
        return self._setting("USERNAME_REQUIRED", True)

    @property
    def USERNAME_MIN_LENGTH(self):
        """
        Minimum username Length
        """
        return self._setting("USERNAME_MIN_LENGTH", 1)

    @property
    def USERNAME_BLACKLIST(self):
        """
        List of usernames that are not allowed
        """
        return self._setting("USERNAME_BLACKLIST", [])

    @property
    def PASSWORD_INPUT_RENDER_VALUE(self):
        """
        render_value parameter as passed to PasswordInput fields
        """
        return self._setting("PASSWORD_INPUT_RENDER_VALUE", False)

    @property
    def ADAPTER(self):
        return self._setting('ADAPTER',
                             'allauth.account.adapter.DefaultAccountAdapter')

    @property
    def LOGOUT_REDIRECT_URL(self):
        return self._setting('LOGOUT_REDIRECT_URL', '/')

    @property
    def LOGOUT_ON_GET(self):
        return self._setting('LOGOUT_ON_GET', False)

    @property
    def USER_MODEL_USERNAME_FIELD(self):
        return self._setting('USER_MODEL_USERNAME_FIELD', 'username')

    @property
    def USER_MODEL_EMAIL_FIELD(self):
        return self._setting('USER_MODEL_EMAIL_FIELD', 'email')

    @property
    def FORMS(self):
        return self._setting('FORMS', {})


# Ugly? Guido recommends this himself ...
# http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
import sys
app_settings = AppSettings('ACCOUNT_')
app_settings.__name__ = __name__
sys.modules[__name__] = app_settings
