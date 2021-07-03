from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from .serializers import UserPasswordChangeSerializer, UserSerializer
from .utils import IsSuperUser
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class ManageUsers(viewsets.ViewSet):
    serializer_class = UserSerializer
    queryset = UserModel.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]

    def create(self, request):
        """
        Register New User
        """
        db = self.serializer_class(data=request.data)
        if db.is_valid():
            db.save()
            return Response(db.data)
        else:
            return Response(db.errors)

    @action(detail=True, methods=["delete"])
    def deactivate(self, request, pk):
        try:
            user = UserModel.objects.get(id=pk)
            user.is_active = False
            user.save()
            return Response("", status.HTTP_204_NO_CONTENT)
        except UserModel.DoesNotExist:
            return Response(
                {"error": f"user {pk} does not exists"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ChangePassword(APIView):
    """
    Change users own password. User needs to be logged in!
    """

    permission_classes = [permissions.IsAuthenticated, IsSuperUser]

    def post(self, request, format="json"):
        """
        Change password! Current and new password should be provided and user should be
        authenticated with token as well!
        """
        serializer = UserPasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data["current_password"]):
                return Response(
                    "Current password is not correct!",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(serializer.data["new_password"])
            user.save()
            return Response("Password Changed Successfully!", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
