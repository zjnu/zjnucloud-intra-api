from django.http import (HttpRequest, HttpResponseRedirect,
                         HttpResponsePermanentRedirect)
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.views.generic.edit import FormView
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator

from .utils import (get_next_redirect_url, complete_binding,
                    get_login_redirect_url, passthrough_next_redirect_url,)
from .exceptions import ImmediateHttpResponse
from emis.binding.forms import BindingForm
from emis.models import Token, EmisUser
from emis.serializers import TokenSerializer
from emis.core import Session
from emis.core import STATUS_SUCCESS

from .adapter import get_adapter
from collections import OrderedDict

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters('password', 'password1', 'password2'))


def _ajax_response(request, response, form=None):
    if request.is_ajax():
        if (isinstance(response, HttpResponseRedirect)
                or isinstance(response, HttpResponsePermanentRedirect)):
            redirect_to = response['Location']
        else:
            redirect_to = None
        response = get_adapter().ajax_response(request,
                                               response,
                                               form=form,
                                               redirect_to=redirect_to)
    return response


class RedirectAuthenticatedUserMixin(object):
    def dispatch(self, request, *args, **kwargs):
        # WORKAROUND: https://code.djangoproject.com/ticket/19316
        self.request = request
        # (end WORKAROUND)
        if request.user.is_authenticated():
            redirect_to = self.get_authenticated_redirect_url()
            response = HttpResponseRedirect(redirect_to)
            return response
        else:
            response = super(RedirectAuthenticatedUserMixin,
                             self).dispatch(request,
                                            *args,
                                            **kwargs)
        return response

    def get_authenticated_redirect_url(self):
        redirect_field_name = self.redirect_field_name
        return get_login_redirect_url(self.request,
                                      url=self.get_success_url(),
                                      redirect_field_name=redirect_field_name)


class AjaxCapableProcessFormViewMixin(object):

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            response = self.form_valid(form)
        else:
            response = self.form_invalid(form)
        return _ajax_response(self.request, response, form=form)


class CloseableSignupMixin(object):
    template_name_signup_closed = "account/signup_closed.html"

    def dispatch(self, request, *args, **kwargs):
        # WORKAROUND: https://code.djangoproject.com/ticket/19316
        self.request = request
        # (end WORKAROUND)
        try:
            if not self.is_open():
                return self.closed()
        except ImmediateHttpResponse as e:
            return e.response
        return super(CloseableSignupMixin, self).dispatch(request,
                                                          *args,
                                                          **kwargs)

    def is_open(self):
        return get_adapter().is_open_for_signup(self.request)

    def closed(self):
        response_kwargs = {
            "request": self.request,
            "template": self.template_name_signup_closed,
        }
        return self.response_class(**response_kwargs)


class SignupView(RedirectAuthenticatedUserMixin, CloseableSignupMixin,
                 AjaxCapableProcessFormViewMixin, FormView):
    form_class = BindingForm
    redirect_field_name = "next"
    success_url = None

    @sensitive_post_parameters_m
    def dispatch(self, request, *args, **kwargs):
        return super(SignupView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # Explicitly passed ?next= URL takes precedence
        ret = (get_next_redirect_url(self.request,
                                     self.redirect_field_name)
               or self.success_url)
        return ret

    def get_context_data(self, **kwargs):
        form = kwargs['form']
        form.fields["email"].initial = self.request.session \
            .get('account_verified_email', None)
        ret = super(SignupView, self).get_context_data(**kwargs)
        login_url = passthrough_next_redirect_url(self.request,
                                                  reverse("account_login"),
                                                  self.redirect_field_name)
        redirect_field_name = self.redirect_field_name
        redirect_field_value = self.request.REQUEST.get(redirect_field_name)
        ret.update({"login_url": login_url,
                    "redirect_field_name": redirect_field_name,
                    "redirect_field_value": redirect_field_value})
        return ret

signup = SignupView.as_view()


class BindingView(APIView, SignupView):
    """
    Accepts the credentials and creates a new user
    if user does not exist already
    Return the REST Token if the credentials are valid and authenticated.
    Calls complete_signup method

    Accept the following POST parameters: username, password
    Return the REST Framework Token Object's key.
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')
    token_model = Token
    serializer_class = TokenSerializer

    def get(self, *args, **kwargs):
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def put(self, *args, **kwargs):
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_object(self, pk):
        try:
            return EmisUser.objects.get(pk=pk)
        except EmisUser.DoesNotExist:
            raise Http404

    def form_valid(self, form):
        self.user = form.save(self.request)
        self.token, created = self.token_model.objects.get_or_create(
            user=self.user
        )
        if isinstance(self.request, HttpRequest):
            request = self.request
        else:
            request = self.request._request

        return complete_binding(request, self.user,
                           self.get_success_url())

    def post(self, request, *args, **kwargs):
        """
        Create authorized user and return the generated token
        """
        self.initial = {}
        self.response_data = OrderedDict()
        self.request.POST = self.request.data.copy()
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)
        if not self.emis_valid(self.request.POST):
            # request EMIS username or password is invalid
            return self.get_response_with_emis_errors()
        if self.form.is_valid():
            self.form_valid(self.form)
            return self.get_response()
        else:
            return self.get_response_with_errors()

    def delete(self, request, *args, **kwargs):
        self.request.POST = self.request.data.copy()
        if self.emis_user_delete(self.request.POST):
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_response(self):
        # serializer = self.serializer_class(instance=self.token)
        self.response_data['token'] = self.token.key
        return Response(self.response_data, status=status.HTTP_201_CREATED)

    def get_response_with_errors(self):
        return Response(self.form.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_response_with_emis_errors(self):
        return Response(self.response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get_form_class(self):
        return BindingForm

    def emis_valid(self, data):
        try:
            emis_username = data['username']
            emis_password = data['password']
            self.status, self.message = Session(username=emis_username,
                              password=emis_password).login()
            self.response_data['status'] = self.status
            self.response_data['message'] = self.message
            if self.status == STATUS_SUCCESS:
                return True
        except MultiValueDictKeyError:
            return False
        return False

    def emis_user_delete(self, data):
        try:
            emis_username = data['username']
            user = self.get_object(emis_username)
            user.delete()
            return True
        except MultiValueDictKeyError:
            return False
