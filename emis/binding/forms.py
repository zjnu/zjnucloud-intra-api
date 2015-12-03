import warnings
from django import forms
from django.utils.translation import ugettext_lazy as _

from .adapter import EmisAccountAdapter
from emis.models import BmobUser


class BaseForm(forms.Form):
    """
    Invoked at signup time to complete the signup of the user.
    """
    def signup(self, request, user):
        pass


class BindingForm(BaseForm):

    username = forms.CharField(label=_("Username"),)
    password = forms.CharField(label=_("Password"),)
    bmob = forms.CharField(label=_("BmobUser"),)

    def __init__(self, *args, **kwargs):
        super(BindingForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(BindingForm, self).clean()
        return self.cleaned_data

    def save(self, request):
        adapter = EmisAccountAdapter()
        # First create BmobUser
        bmob_user = adapter.new_bmob_user(request)
        adapter.save_bmob_user(request, bmob_user, self)
        # Then save EMIS user
        user = adapter.new_user(request)
        adapter.save_user(request, user, bmob_user, self)
        self.custom_signup(request, user)
        return user

    def custom_signup(self, request, user):
        custom_form = super(BindingForm, self)
        if hasattr(custom_form, 'signup') and callable(custom_form.signup):
            custom_form.signup(request, user)
        else:
            warnings.warn("The custom signup form must offer"
                          " a `def signup(self, request, user)` method",
                          DeprecationWarning)
            # Historically, it was called .save, but this is confusing
            # in case of ModelForm
            custom_form.save(user)
