from collections import OrderedDict

from rest_framework import serializers

from onecard.models import Token, OneCardCharge, OneCardUser


class BaseOneCardSerializer(serializers.BaseSerializer):

    def to_representation(self, data):
        return data


class BindingSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=2048)
    bmob = serializers.CharField(max_length=255)


class OneCardDetailsSerializer(BaseOneCardSerializer):
    pass


class OneCardChargeSerializer(serializers.Serializer):
    """
    Serializer for OneCardCharge model when charge
    """
    amount = serializers.CharField()
    payPassword = serializers.CharField()

    def create(self, validated_data):
        return OneCardCharge.objects.create(**validated_data)

    def to_internal_value(self, data):
        code = data.get('code')
        message = data.get('message')
        result = data.get('result')
        username = data.get('username')
        amount = data.get('amount')

        user = OneCardUser.objects.get(username=username)
        return {
            'code': code,
            'message': message,
            'result': result,
            'user': user,
            'amount': amount,
        }

    def to_representation(self, instance):
        ret = OrderedDict()
        ret['code'] = instance.code
        ret['message'] = instance.message
        ret['result'] = instance.result
        ret['user'] = instance.user.username
        ret['amount'] = instance.amount
        return ret


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model in OneCard
    """
    class Meta:
        model = Token
        fields = ('key',)
