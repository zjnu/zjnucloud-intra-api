from rest_framework import serializers

from onecard.models import Token


class BaseOneCardSerializer(serializers.BaseSerializer):

    def to_representation(self, data):
        return data


class BindingSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=2048)
    bmob = serializers.CharField(max_length=255)


class OneCardDetailsSerializer(BaseOneCardSerializer):
    pass


class OneCardBalanceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    payPassword = serializers.CharField(max_length=2048, required=True)

    def to_representation(self, value):
        return value


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model in OneCard
    """

    class Meta:
        model = Token
        fields = ('key',)
