from collections import OrderedDict

from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from onepay import core
from onepay.adapter import get_adapter
from onepay.authentication import OnePayTokenAuthentication
from onepay.core import STATUS_SUCCESS, MSG_ONEPAY_BIND_SUCCESS
from onepay.models import OnePayUser, Token
from . import app_settings

from common.models import BmobUser


class BindingView(APIView):
    CODE_PARAMS_ERROR = '400'
    MESSAGE_PARAMS_ERROR = '请求参数错误，请检查'

    permission_classes = (AllowAny,)
    authentication_classes = ()
    allowed_methods = ('POST', 'DELETE')
    token_model = Token

    def get(self, *args, **kwargs):
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def put(self, *args, **kwargs):
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        """
        Create and bind new user and return the generated token
        """
        self.initial = {}
        self.response_data = OrderedDict()

        # Check form data
        if not request.data.get('username') or not request.data.get('password') \
                or not request.data.get('bmob'):
            return self.get_response_with_params_errors()

        # Check account validation
        adapter = get_adapter()
        if not self.onepay_account_valid():
            return self.get_response_with_onepay_errors()

        # Create new association between Bmob user and OnePay user
        existed, onepay_user, bmob_user = adapter.get_association(request.data)
        if not existed:
            # Check if exceed Bmob account bind times limit
            if not self.bmob_limit_valid(request.data):
                return self.get_response_with_onepay_errors()

            # Check if exceed OnePay account bind times limit
            if not self.onepay_limit_valid(request.data):
                return self.get_response_with_onepay_errors()

            self.perform_binding(request.data)
        else:
            self.token, created = self.token_model.objects.get_or_create(user=onepay_user)
            self.response_data['message'] = MSG_ONEPAY_BIND_SUCCESS

        return self.get_response()

    def delete(self, request, *args, **kwargs):
        pass

    def perform_binding(self, data):
        """
        Save user objects and generate token
        :return: void
        """
        adapter = get_adapter()
        self.bmob_user = adapter.get_bmob_user(data['bmob'])
        self.onepay_user = adapter.get_onepay_user(data['username'])
        adapter.save_bmob_user(self.bmob_user, data)
        adapter.save_onepay_user(self.onepay_user, data)
        # Add Many-to-Many relation
        self.onepay_user.bmobusers.add(self.bmob_user)
        # Gen token
        self.token, created = self.token_model.objects.get_or_create(user=self.onepay_user)
        self.response_data['message'] = MSG_ONEPAY_BIND_SUCCESS

    def onepay_account_valid(self):
        """
        Perform OnePay account validation
        :return: Boolean
        """
        try:
            self.response_data['code'], self.response_data['message'] = core.Session(
                self.request.data['username'],
                self.request.data['password']
            ).login()

            return True if self.response_data['code'] == STATUS_SUCCESS else False
        except MultiValueDictKeyError:
            return False

    def bmob_limit_valid(self, data):
        """
        Validate that BmobUser has not exceeded limits,
        value comes from app_settings.BMOB_USER_LIMIT
        :param: data request.data
        :return True if not exceed limits
        """
        # TODO: BmobUser limit & append error msg
        return True

    def onepay_limit_valid(self, data):
        """
        Validate that OnePayUser has not exceeded limits,
        value comes from app_settings.ONEPAY_USER_LIMIT
        :param: data request.data
        :return True if not exceed limits
        """
        # TODO: OnePayUser limit & append error msg
        return True

    def append_message(self, code, message):
        self.response_data['code'] = code
        self.response_data['message'] = message

    def get_response(self):
        self.response_data['token'] = self.token.key
        return Response(self.response_data, status=status.HTTP_200_OK)

    def get_response_with_onepay_errors(self):
        self.response_data['token'] = None
        return Response(self.response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get_response_with_params_errors(self):
        return Response(data={
            'code': self.CODE_PARAMS_ERROR,
            'message': self.MESSAGE_PARAMS_ERROR,
            'token': None,
        })


class OneCardBalance(APIView):
    allowed_methods = ('GET',)
    authentication_classes = (OnePayTokenAuthentication,)

    def post(self, request, format=None):
        return Response('')
