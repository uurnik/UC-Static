from django.urls import path
from api.net_tools.views import ping, nslookup, traceroute


app_name = "net-tools"

urlpatterns = [
    path("ping-term", ping),
    path("nslookup", nslookup),
    path("traceroute", traceroute),
]
