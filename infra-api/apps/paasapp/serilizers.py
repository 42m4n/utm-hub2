from rest_framework import serializers


class PaasSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, allow_null=False)
