from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class LoginSerializer(TokenObtainPairSerializer):
    username_field = 'username'


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    rol = serializers.ChoiceField(choices=['administrador', 'medico', 'analista'])
    password = serializers.CharField(write_only=True, min_length=8)


