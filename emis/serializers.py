from rest_framework import serializers
from emis.models import Token


class BaseEmisSerializer(serializers.BaseSerializer):

    def to_representation(self, data):
        return data


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model.
    """

    class Meta:
        model = Token
        fields = ('key',)
