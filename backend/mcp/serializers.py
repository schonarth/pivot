from rest_framework import serializers
from .models import OTP, AgentToken


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['code', 'expires_at']
        read_only_fields = ['code', 'expires_at']


class AgentTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentToken
        fields = ['id', 'name', 'origin', 'created_at', 'last_used_at']
        read_only_fields = ['id', 'created_at', 'last_used_at']
