from django.urls import path
from django.conf.urls import url
from .views import ManageUsers, ChangePassword ,UserDetail ,MyTokenObtainPairView
from rest_framework import routers


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

user_router = routers.SimpleRouter()
user_router.register(r"", ManageUsers)
user_router.register(r"", UserDetail)



app_name = "users"


urlpatterns = [
    path("change_password/", ChangePassword.as_view(), name="change_password"),
    path("token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urlpatterns += user_router.urls
