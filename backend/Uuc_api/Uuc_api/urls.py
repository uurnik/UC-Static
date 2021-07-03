from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("api/", include("api.urls")),
    path("api/users/", include("api.users.urls")),
    path("api/net_tools/", include("api.net_tools.urls")),
]
