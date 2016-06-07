from rest_auth.app_settings import serializers
from onepay.models import Token


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model in OnePay
    """

    class Meta:
        model = Token
        fields = ('key',)
