from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from onepay.models import Token, OnePayUser


class OnePayTokenAuthentication(BaseAuthentication):
    """
    EMIS token authentication.

    Clients should authenticate by passing the EMIS username and passord in request data,
    as well as the token key in the "Authorization" HTTP header
    """
    model = Token

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        data = request.data

        if not auth or auth[0].lower() != b'token':
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except OnePayUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)
        except MultiValueDictKeyError:
            raise exceptions.AuthenticationFailed('Insufficient params')
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.select_related('user').get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (token.user, token)




