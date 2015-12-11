from django.contrib.auth import get_user_model
from django.utils.http import urlencode

from .adapter import get_adapter


def get_next_redirect_url(request, redirect_field_name="next"):
    """
    Returns the next URL to redirect to, if it was explicitly passed
    via the request.
    """
    redirect_to = request.REQUEST.get(redirect_field_name)
    if not get_adapter().is_safe_url(redirect_to):
        redirect_to = None
    return redirect_to


def get_login_redirect_url(request, url=None, redirect_field_name="next"):
    redirect_url \
        = (url
           or get_next_redirect_url(request,
                                    redirect_field_name=redirect_field_name)
           or get_adapter().get_login_redirect_url(request))
    return redirect_url


def passthrough_next_redirect_url(request, url, redirect_field_name):
    assert url.find("?") < 0  # TODO: Handle this case properly
    next_url = get_next_redirect_url(request, redirect_field_name)
    if next_url:
        url = url + '?' + urlencode({redirect_field_name: next_url})
    return url


def user_field(user, field, *args):
    """
    Gets or sets (optional) user model fields. No-op if fields do not exist.
    """
    if field and hasattr(user, field):
        if args:
            # Setter
            v = args[0]
            if v:
                User = get_user_model()
                v = v[0:User._meta.get_field(field).max_length]
            setattr(user, field, v)
        else:
            # Getter
            return getattr(user, field)


def user_username(user, *args):
    return user_field(user, 'username', *args)


def user_count(user, *args):
    if args and hasattr(user, 'count'):
        setattr(user, 'count', args[0])


def user_bmobuser(user, *args):
    if args:
            # Setter
            v = args[0]
            if v:
                setattr(user, 'bmob_account', v)
    else:
        # Getter
        return getattr(user, 'bmob_account')


def complete_binding(request, user, success_url,
                    signal_kwargs=None):
    return True
    # if signal_kwargs is None:
    #     signal_kwargs = {}
    # signals.user_signed_up.send(sender=user.__class__,
    #                             request=request,
    #                             user=user,
    #                             **signal_kwargs)
    # return perform_login(request, user,
    #                      email_verification=email_verification,
    #                      signup=True,
    #                      redirect_url=success_url,
    #                      signal_kwargs=signal_kwargs)
