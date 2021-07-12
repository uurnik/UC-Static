from rest_framework import serializers
from api.models import Account
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
import datetime
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    def to_representation(self, data):
        data = super(UserSerializer, self).to_representation(data)
        old_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        new_format = "%d-%m-%Y %H:%M"
        data["last_login"] = new_datetime_str = datetime.datetime.strptime(
            data["last_login"], old_format
        ).strftime(new_format) + " UTC"
        return data


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
            "is_superuser",
            "is_staff",
            "is_active",
            "last_login",
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


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        user_db = UserModel.objects.get(username=self.user.username)
        user_db.last_login = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        user_db.save()

        return data
