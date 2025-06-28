# serializers.py
from rest_framework import serializers
from .models import DeviceLogin

class DeviceLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceLogin
        fields = ['hostname', 'email', 'token', 'registered_at']
