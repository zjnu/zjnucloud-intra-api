from collections import OrderedDict

from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from onecard import core
from onecard.adapter import get_adapter
from onecard.authentication import OneCardTokenAuthentication
from onecard.core import STATUS_SUCCESS, STATUS_EXCEED_BMOB_BIND_TIMES_LIMIT, \
    STATUS_EXCEED_ONECARD_BIND_TIMES_LIMIT, MSG_ONECARD_BIND_SUCCESS, \
    MSG_EXCEED_BMOB_BIND_TIMES_LIMIT, MSG_EXCEED_ONECARD_BIND_TIMES_LIMIT
from onecard.models import Token
from onecard.serializers import BaseOneCardSerializer, BindingSerializer, OneCardDetailsSerializer, \
    OneCardBalanceSerializer

CODE_PARAMS_ERROR = '400'
MESSAGE_PARAMS_ERROR = '请求参数错误，请检查'


class BindingView(GenericAPIView):
    """
    Bind a OneCardUser to the user system (BmobUser) and return the token
    """
    allowed_methods = ('POST', 'DELETE')
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = BindingSerializer
    token_model = Token

    def post(self, request, *args, **kwargs):
        """
        Create and bind new user and return the generated token
        """
        return self.do_post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Unbind the user and delete its relation
        """
        return self.do_delete(request.data)

    def do_post(self, request, *args, **kwargs):
        self.initial = {}
        self.response_data = OrderedDict()

        # Check form data
        if not request.data.get('username') or not request.data.get('password') \
                or not request.data.get('bmob'):
            return self.get_response_with_params_errors()

        # Check account validation
        if not self.onecard_account_valid():
            return self.get_response_with_account_auth_errors()

        # Create new association between Bmob user and OneCard user
        adapter = get_adapter()
        existed, onecard_user, bmob_user = adapter.get_association(request.data)

        if not existed:
            # Check if exceed Bmob account bind times limit
            if not self.bmob_limit_valid(request.data):
                return self.get_response_with_bmob_limit_errors()

            # Check if exceed OneCard account bind times limit
            if not self.onecard_limit_valid(request.data):
                return self.get_response_with_onecard_limit_errors()

            self.perform_binding(request.data)
        else:
            self.token, created = self.token_model.objects.get_or_create(user=onecard_user)

        return self.get_response()

    def do_delete(self, data):
        adapter = get_adapter()
        if adapter.delete_onecard_user(data):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return self.get_response_with_not_found_errors()

    def perform_binding(self, data):
        """
        Save user objects and generate token
        :return: void
        """
        adapter = get_adapter()
        self.bmob_user = adapter.get_bmob_user(data['bmob'])
        self.onecard_user = adapter.get_onecard_user(data['username'])
        adapter.save_bmob_user(self.bmob_user, data)
        adapter.save_onecard_user(self.onecard_user, data)
        # Add Many-to-Many relation
        self.onecard_user.bmobusers.add(self.bmob_user)
        # Gen token
        self.token, created = self.token_model.objects.get_or_create(user=self.onecard_user)
        self.response_data['message'] = MSG_ONECARD_BIND_SUCCESS

    def onecard_account_valid(self):
        """
        Perform OneCard account validation
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
        # TODO: BmobUser limit (maybe add a field 'onecard_count'?) & append error msg
        return True

    def onecard_limit_valid(self, data):
        """
        Validate that OneCardUser has not exceeded limits,
        value comes from app_settings.OneCard_USER_LIMIT
        :param: data request.data
        :return True if not exceed limits
        """
        # TODO: OneCardUser limit & append error msg
        return True

    def append_message(self, code, message):
        self.response_data['code'] = code
        self.response_data['message'] = message

    def get_response(self):
        self.append_message(STATUS_SUCCESS, MSG_ONECARD_BIND_SUCCESS)
        self.response_data['token'] = self.token.key
        return Response(self.response_data, status=status.HTTP_200_OK)

    def get_response_with_account_auth_errors(self):
        self.response_data['token'] = None
        return Response(self.response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get_response_with_bmob_limit_errors(self):
        self.append_message(
            STATUS_EXCEED_BMOB_BIND_TIMES_LIMIT,
            MSG_EXCEED_BMOB_BIND_TIMES_LIMIT
        )
        self.response_data['token'] = None
        return Response(self.response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get_response_with_onecard_limit_errors(self):
        self.append_message(
            STATUS_EXCEED_ONECARD_BIND_TIMES_LIMIT,
            MSG_EXCEED_ONECARD_BIND_TIMES_LIMIT
        )
        self.response_data['token'] = None
        return Response(self.response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get_response_with_params_errors(self):
        return Response(data={
            'code': CODE_PARAMS_ERROR,
            'message': MESSAGE_PARAMS_ERROR,
            'token': None,
        }, status=status.HTTP_400_BAD_REQUEST)

    def get_response_with_not_found_errors(self):
        return Response(status=status.HTTP_404_NOT_FOUND)


class OneCardDetailsList(GenericAPIView):
    """
    Get OneCard account detail information
    """
    allowed_methods = ('GET',)
    authentication_classes = (OneCardTokenAuthentication,)
    serializer_class = OneCardDetailsSerializer

    def get(self, request, username, format=None):
        """
        Get account balance
        """
        data = core.OneCardAccountDetail(username).get_detail()
        serializer = BaseOneCardSerializer(data)
        return Response(serializer.data)


class OneCardBalanceList(GenericAPIView):
    """
    Get OneCard account balance, Post to make a charge
    """
    allowed_methods = ('GET', 'POST')
    authentication_classes = (OneCardTokenAuthentication,)
    serializer_class = OneCardBalanceSerializer

    def get(self, request, username, format=None):
        """
        Get account balance
        """
        data = core.OneCardBalance(username).get_balance()
        serializer = OneCardBalanceSerializer(data)
        return Response(serializer.data)

    def post(self, request, username, format=None):
        """
        Make a charge
        """
        is_amount_valid, amount = core.OneCardBalance.check_amount(request.data.get('amount'))
        pay_password = request.data.get('payPassword')
        if is_amount_valid:
            data = core.OneCardBalance(username).charge(
                amount,
                pay_password,
            )
            serializer = OneCardBalanceSerializer(data)
            return Response(serializer.data)
        else:
            if not amount:
                data = core.get_response_data_without_result(
                    core.STATUS_ONLINE_BANK_CHARGE_INVALID_AMOUNT,
                    core.MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT
                )
            else:
                data = core.get_response_data_without_result(
                    core.STATUS_ONLINE_BANK_CHARGE_AMOUNT_LIMIT,
                    core.MSG_ONLINE_BANK_CHARGE_AMOUNT_LIMIT
                )
            serializer = OneCardBalanceSerializer(data)
            return Response(serializer.data)
