import warnings
from django import forms
from django.utils.translation import ugettext_lazy as _

from .adapter import EmisAccountAdapter


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
        bmob_user = adapter.get_bmob_user(self)
        emis_user = adapter.get_emis_user(self)
        # Save Bmob user
        adapter.save_bmob_user(request, bmob_user, self)
        # Save EMIS user
        adapter.save_emis_user(request, emis_user, self)
        # Associate EMIS user with Bmob user
        emis_user.bmobusers.add(bmob_user)
        self.complete_binding(request, emis_user)
        return emis_user, bmob_user

    def complete_binding(self, request, user):
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
