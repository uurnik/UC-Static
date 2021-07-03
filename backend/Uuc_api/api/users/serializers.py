from rest_framework import serializers
from api.models import Account
from django.contrib.auth.models import User

from django.contrib.auth import get_user_model


UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user

    class Meta:
        model = UserModel
        fields = (
            "id",
            "email",
            "username",
            "password",
        )


class UserPasswordChangeSerializer(serializers.Serializer):
    """
    Serializer just for password change.
    """

    current_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128, min_length=8)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
